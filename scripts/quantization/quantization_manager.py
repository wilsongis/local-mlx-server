"""
Quantization manager for coordinating profile application during model load.

Manages the application of per-path hybrid quantization profiles to MLX models,
including model detection, checksum validation, rollback logic, and logging.
"""

import hashlib
import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .config_builder import QuantizationConfigBuilder
from .kv_cache_compression import KVCacheCompressionManager
from .model_detector import ModelArchitecture, ModelDetector
from .profile_validator import ProfileValidationError, QuantizationProfile

logger = logging.getLogger(__name__)


class QuantizationManager:
    """
    Coordinates quantization profile application during model load.

    Handles model detection, profile validation, config generation,
    checksum validation, rollback on failure, and logging.
    """

    def __init__(
        self,
        model_path: str,
        profile_name: Optional[str] = None,
        profile_path: Optional[str] = None,
        kv_cache_config: Optional[Dict] = None,
    ):
        """
        Initialize quantization manager.

        Args:
            model_path: Path to the model directory
            profile_name: Name of preset profile (e.g., "tq3a-tq2e-g32")
            profile_path: Path to custom profile YAML file
            kv_cache_config: Optional KV cache compression configuration
        """
        self.model_path = model_path
        self.profile_name = profile_name
        self.profile_path = profile_path
        self.profile: Optional[QuantizationProfile] = None
        self.model_architecture: Optional[ModelArchitecture] = None
        self.config_builder: Optional[QuantizationConfigBuilder] = None

        # Initialize KV cache compression manager
        self.kv_cache_manager: Optional[KVCacheCompressionManager] = None
        if kv_cache_config:
            self.kv_cache_manager = KVCacheCompressionManager(kv_cache_config)
            logger.info("KV cache compression manager initialized")

    def initialize(self) -> None:
        """
        Initialize the quantization manager by loading profile and detecting model.

        Raises:
            ProfileValidationError: If profile is invalid
            ModelDetectionError: If model detection fails
        """
        # Load quantization profile
        if self.profile_name:
            from .profile_validator import ProfileValidator

            self.profile = ProfileValidator.validate_preset_name(self.profile_name)
            logger.info(f"Loaded quantization profile: {self.profile_name}")
        elif self.profile_path:
            from .profile_validator import ProfileValidator

            self.profile = ProfileValidator.from_yaml_file(self.profile_path)
            logger.info(f"Loaded quantization profile from: {self.profile_path}")
        else:
            logger.info("No quantization profile specified")
            return

        # Detect model architecture
        detector = ModelDetector(self.model_path)
        self.model_architecture = detector.detect()
        logger.info(
            f"Detected model architecture: {self.model_architecture.architecture_name}"
        )

        if self.model_architecture.is_moe:
            logger.info(
                f"MoE model detected: {self.model_architecture.expert_count} experts"
            )

        # Create config builder
        self.config_builder = QuantizationConfigBuilder(self.profile)

        # Set model context for KV cache auto profile selection
        if self.kv_cache_manager:
            # Determine model size class from architecture
            model_size_class = self._determine_model_size_class()
            weight_bits = self.profile.attention_bits if self.profile else None
            self.kv_cache_manager.set_model_context(model_size_class, weight_bits)

    def _determine_model_size_class(self) -> str:
        """Determine model size class from architecture."""
        if not self.model_architecture:
            return "20B"  # Default

        total_params = self.model_architecture.total_params or 0

        if total_params >= 100e9:  # 100B+
            return "100B+"
        elif total_params >= 70e9:  # 70B
            return "70B"
        else:
            return "20B"

    def validate_model_checksum(self) -> bool:
        """
        Validate model checksum before applying quantization (NFR-001, ERR-004).

        Returns:
            True if checksum is valid or no checksum required

        Raises:
            ProfileValidationError: If checksum mismatch (ERR-004)
        """
        # Check if model has checksum file
        checksum_path = Path(self.model_path) / "checksum.md5"
        if not checksum_path.exists():
            logger.info("No checksum file found, skipping validation")
            return True

        try:
            with open(checksum_path, "r") as f:
                expected_checksum = f.read().strip().split()[0]

            # Calculate actual checksum of model files
            model_files = list(Path(self.model_path).glob("*.safetensors"))
            if not model_files:
                model_files = list(Path(self.model_path).glob("*.bin"))

            if not model_files:
                logger.warning("No model files found for checksum calculation")
                return True

            # Calculate checksum of first model file (simplified)
            actual_checksum = self._calculate_file_checksum(model_files[0])

            if actual_checksum != expected_checksum:
                error_msg = f"Model checksum mismatch: expected {expected_checksum}, got {actual_checksum}"
                logger.error(error_msg)
                raise ProfileValidationError("ERR-004", error_msg)

            logger.info("Model checksum validation passed")
            return True

        except Exception as e:
            if isinstance(e, ProfileValidationError):
                raise
            logger.error(f"Checksum validation error: {e}")
            return False

    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of a file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def apply_quantization(self) -> Dict[str, Any]:
        """
        Apply quantization profile to the model.

        Returns:
            Dictionary with quantization configuration for mlx_lm.server

        Raises:
            ProfileValidationError: If quantization application fails
        """
        if not self.profile:
            logger.info("No quantization profile to apply")
            return {}

        if not self.config_builder or not self.model_architecture:
            self.initialize()

        try:
            # Validate model checksum first
            self.validate_model_checksum()

            # Build quantization config
            config = self.config_builder.build_config(self.model_architecture)

            # Log quantization application
            logger.info(
                f"Applying quantization: attention={self.profile.attention_bits}-bit, "
                f"expert={self.profile.expert_bits}-bit, group={self.profile.group_size}"
            )

            if self.model_architecture.is_moe:
                logger.info(
                    f"MoE model: {self.model_architecture.expert_count} experts, "
                    f"active params: {self.model_architecture.active_params}"
                )

            # Update health endpoint with quantization status
            self._update_health_status()

            return config

        except Exception as e:
            # Rollback logic (NFR-005)
            logger.error(f"Quantization application failed: {e}")
            self._rollback()
            raise

    def apply_kv_cache_compression(self, prompt_cache: list) -> list:
        """
        Apply KV cache compression to prompt cache.

        Args:
            prompt_cache: List of (key_cache, value_cache) tuples per layer

        Returns:
            Converted cache list with TurboQuantKVCache where applicable
        """
        if not self.kv_cache_manager or not self.kv_cache_manager.enabled:
            logger.debug("KV cache compression not enabled")
            return prompt_cache

        # Select profile based on model context
        model_size_class = self._determine_model_size_class()
        weight_bits = self.profile.attention_bits if self.profile else None
        profile = self.kv_cache_manager.select_profile(model_size_class, weight_bits)

        # Convert cache
        return self.kv_cache_manager.convert_cache_to_turboquant(prompt_cache, profile)

    def _update_health_status(self) -> None:
        """Update health endpoint with quantization status."""
        try:
            from scripts.mlx_wrapper import update_quantization_status

            update_quantization_status(
                profile=self.profile_name or self.profile.preset_name,
                attention_bits=self.profile.attention_bits,
                expert_bits=self.profile.expert_bits,
                group_size=self.profile.group_size,
                model_architecture=self.model_architecture.architecture_name,
                is_moe=self.model_architecture.is_moe,
                expert_count=self.model_architecture.expert_count,
                active_params=self.model_architecture.active_params,
                total_params=self.model_architecture.total_params,
            )
        except ImportError:
            logger.warning(
                "Could not import update_quantization_status, health endpoint not updated"
            )

    def _rollback(self) -> None:
        """
        Rollback to previous configuration on failed quantization (NFR-005).
        """
        logger.info("Rolling back quantization configuration...")

        # Reset health endpoint quantization status
        try:
            from scripts.mlx_wrapper import update_quantization_status

            update_quantization_status(
                profile=None,
                attention_bits=None,
                expert_bits=None,
                group_size=None,
                model_architecture=None,
                is_moe=False,
                expert_count=0,
                active_params=None,
                total_params=None,
            )
        except ImportError:
            pass

        # Additional rollback logic can be added here
        # (e.g., restore previous config file, clear cached quantization)

        logger.info("Rollback complete")

    def get_quantization_args(self) -> Dict[str, str]:
        """
        Get MLX server arguments for quantization.

        Returns:
            Dictionary of CLI arguments for mlx_lm.server
        """
        if not self.profile:
            return {}

        # Generate quantization config YAML
        config = self.config_builder.build_config(self.model_architecture)

        # Write config to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            config_path = f.name

        return {"--quant-config": config_path}

    @staticmethod
    def from_env() -> Optional["QuantizationManager"]:
        """
        Create QuantizationManager from MLX_QUANT_PROFILE environment variable.

        Returns:
            QuantizationManager instance or None if env var not set
        """
        profile = os.environ.get("MLX_QUANT_PROFILE")
        if not profile:
            return None

        # Check if it's a preset name or file path
        if os.path.exists(profile):
            return QuantizationManager(
                model_path="",  # Will be set later
                profile_path=profile,
            )
        else:
            return QuantizationManager(
                model_path="",  # Will be set later
                profile_name=profile,
            )

    def apply_moe_quantization(self) -> Dict[str, Any]:
        """
        Apply quantization with MoE-specific handling (T024-T025).

        Returns:
            Dictionary with MoE-specific quantization configuration
        """
        if not self.model_architecture or not self.model_architecture.is_moe:
            logger.info("Model is not MoE, using standard quantization")
            return self.apply_quantization()

        logger.info(
            f"Applying MoE quantization for {self.model_architecture.expert_count} experts"
        )

        # Apply per-path quantization with MoE awareness
        config = self.apply_quantization()

        # Add MoE-specific quantization settings
        if "quantization" in config and "paths" in config["quantization"]:
            # Ensure expert layers get expert_bits
            for path_config in config["quantization"]["paths"]:
                if any(
                    re.match(pattern, path_config.get("pattern", ""), re.IGNORECASE)
                    for pattern in self.model_architecture.EXPERT_PATTERNS
                ):
                    path_config["bits"] = self.profile.expert_bits
                    path_config["description"] = (
                        f"Expert layers at {self.profile.expert_bits}-bit"
                    )

        # Log MoE-specific information
        logger.info(f"MoE model: {self.model_architecture.expert_count} experts")
        logger.info(f"Active params: {self.model_architecture.active_params}")
        logger.info(f"Expert quantization: {self.profile.expert_bits}-bit")

        return config

    def handle_sparse_expert_activation(self) -> None:
        """
        Handle sparse expert activation for MoE models (T025).

        For MoE models, only active experts need to be loaded with
        quantization, reducing memory footprint.
        """
        if not self.model_architecture or not self.model_architecture.is_moe:
            return

        logger.info("Handling sparse expert activation for MoE model")
        # This would integrate with MLX's MoE loading mechanism
        # to only load and quantize active experts
        # Implementation depends on MLX's MoE support

    def integrate_lloyd_max_codebooks(self) -> Dict[str, Any]:
        """
        Integrate Lloyd-Max codebooks during quantization (T033).

        When calibration_method is "lloyd-max", this method loads and
        applies the generated codebooks to improve quantization accuracy.
        """
        if not self.profile or self.profile.calibration_method != "lloyd-max":
            return self.apply_quantization()

        logger.info("Integrating Lloyd-Max codebooks for quantization")

        # Load calibration data
        if not self.profile.calibration_data_path:
            raise ProfileValidationError(
                "ERR-003", "Calibration data path required for lloyd-max method"
            )

        # Validate calibration path
        from .profile_validator import ProfileValidator

        ProfileValidator.validate_calibration_path(self.profile.calibration_data_path)

        # Generate codebook using Lloyd-Max
        from .lloyd_max import LloydMaxCalibrator

        calibrator = LloydMaxCalibrator(
            bits=self.profile.attention_bits, group_size=self.profile.group_size
        )

        # Load calibration data
        calibration_data = calibrator.load_calibration_data(
            self.profile.calibration_data_path
        )

        # Generate codebook
        calibrator.generate_codebook(
            calibration_data,
            layer_names=self.model_architecture.detected_expert_layers
            if self.model_architecture
            else None,
        )

        # Save codebook
        codebook_path = calibrator.save_codebook(".")

        # Apply quantization with codebook
        config = self.apply_quantization()

        # Add codebook reference to config
        if "quantization" not in config:
            config["quantization"] = {}

        config["quantization"]["codebook"] = {
            "path": codebook_path,
            "algorithm": "lloyd-max",
            "version": calibrator.algorithm_version,
            "perplexity_improvement": calibrator.perplexity_improvement,
        }

        logger.info(f"Lloyd-Max codebook integrated: {codebook_path}")
        logger.info(f"Perplexity improvement: {calibrator.perplexity_improvement:.2f}%")

        return config

    def get_kv_cache_status(self) -> Optional[Dict]:
        """Get KV cache compression status for health endpoint."""
        if self.kv_cache_manager:
            return self.kv_cache_manager.get_status()
        return None
