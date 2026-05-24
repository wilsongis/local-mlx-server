"""
Configuration builder for generating MLX quantization config from QuantizationProfile.

Generates YAML configuration files that can be passed to mlx_lm.server --quant-config.
"""

import logging
import os
from typing import Any, Dict, Optional

import yaml

from .kv_cache_profiles import (
    V2_SPEED_PROFILE,
    V3_QUALITY_PROFILE,
    CompressionProfile,
    create_auto_profile,
)
from .profile_validator import ProfileValidationError, QuantizationProfile

logger = logging.getLogger(__name__)


class QuantizationConfigBuilder:
    """Builds MLX quantization configuration from QuantizationProfile."""

    @staticmethod
    def parse_kv_cache_config(kv_cache_config: dict) -> Optional[CompressionProfile]:
        """Parse KV cache configuration from profiles.yaml.

        Args:
            kv_cache_config: Dict with keys: enabled, profile, default_bits,
                               default_group_size, fallback_on_error

        Returns:
            CompressionProfile based on configuration, or None if disabled
        """
        if not kv_cache_config.get("enabled", False):
            logger.debug("KV cache compression disabled in config")
            return None

        profile_name = kv_cache_config.get("profile", "auto")

        if profile_name == "auto":
            profile = create_auto_profile()
        elif profile_name == "v2-speed":
            profile = V2_SPEED_PROFILE
        elif profile_name == "v3-quality":
            profile = V3_QUALITY_PROFILE
        else:
            # Load from kv_cache_profiles.yaml (not implemented yet)
            logger.warning(f"Custom profile '{profile_name}' not found, using auto")
            profile = create_auto_profile()

        # Override defaults with config values
        if "default_bits" in kv_cache_config:
            profile.bits = kv_cache_config["default_bits"]
        if "default_group_size" in kv_cache_config:
            profile.group_size = kv_cache_config["default_group_size"]

        logger.info(
            f"Parsed KV cache config: profile={profile.name}, bits={profile.bits}"
        )
        return profile

    def __init__(self, profile: QuantizationProfile):
        """
        Initialize builder with a validated quantization profile.

        Args:
            profile: Validated QuantizationProfile instance
        """
        self.profile = profile

    def build_config(self, model_architecture: Optional[Any] = None) -> Dict[str, Any]:
        """
        Build MLX quantization configuration dictionary.

        Args:
            model_architecture: Optional ModelArchitecture for per-path optimization

        Returns:
            Dictionary containing MLX quantization configuration
        """
        config = {
            "version": self.profile.version,
            "quantization": {"type": "per_path_hybrid", "paths": []},
        }

        # Add attention layer config
        attention_config = {
            "pattern": "attention.*",
            "bits": self.profile.attention_bits,
            "group_size": self.profile.group_size,
            "description": f"Attention layers at {self.profile.attention_bits}-bit",
        }
        config["quantization"]["paths"].append(attention_config)

        # Add expert layer config (if MoE model detected)
        if model_architecture and model_architecture.is_moe:
            expert_config = {
                "pattern": ".*expert.*",
                "bits": self.profile.expert_bits,
                "group_size": self.profile.group_size,
                "description": f"Expert layers at {self.profile.expert_bits}-bit",
            }
            config["quantization"]["paths"].append(expert_config)
        else:
            # For non-MoE models, apply expert bits to FFN layers
            ffn_config = {
                "pattern": "ffn.*|mlp.*",
                "bits": self.profile.expert_bits,
                "group_size": self.profile.group_size,
                "description": f"FFN/MLP layers at {self.profile.expert_bits}-bit",
            }
            config["quantization"]["paths"].append(ffn_config)

        # Add calibration config if using Lloyd-Max
        if self.profile.calibration_method == "lloyd-max":
            config["quantization"]["calibration"] = {
                "method": "lloyd-max",
                "data_path": self.profile.calibration_data_path,
                "algorithm_version": "V3",
            }

        return config

    def to_yaml(self, output_path: Optional[str] = None) -> str:
        """
        Generate YAML string or write to file.

        Args:
            output_path: Optional path to write YAML file

        Returns:
            YAML string representation of the configuration

        Raises:
            ProfileValidationError: If file cannot be written
        """
        config = self.build_config()

        yaml_str = yaml.dump(config, default_flow_style=False, sort_keys=False)

        if output_path:
            try:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "w") as f:
                    f.write(yaml_str)
            except Exception as e:
                raise ProfileValidationError(
                    "ERR-001", f"Failed to write config to {output_path}: {str(e)}"
                )

        return yaml_str

    @staticmethod
    def from_profile_name(profile_name: str) -> "QuantizationConfigBuilder":
        """
        Create builder from a preset profile name.

        Args:
            profile_name: Name of preset (e.g., "tq3a-tq2e-g32")

        Returns:
            QuantizationConfigBuilder instance

        Raises:
            ProfileValidationError: If profile not found or invalid
        """
        from .profile_validator import ProfileValidator

        profile = ProfileValidator.validate_preset_name(profile_name)
        return QuantizationConfigBuilder(profile)

    @staticmethod
    def from_yaml_file(profile_path: str) -> "QuantizationConfigBuilder":
        """
        Create builder from a YAML profile file.

        Args:
            profile_path: Path to YAML profile file

        Returns:
            QuantizationConfigBuilder instance

        Raises:
            ProfileValidationError: If file invalid or not found
        """
        from .profile_validator import ProfileValidator

        profile = ProfileValidator.from_yaml_file(profile_path)
        return QuantizationConfigBuilder(profile)
