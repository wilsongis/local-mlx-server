"""KV Cache Compression Manager.

This module implements KV cache compression using TurboQuant V2/V3 techniques
for MLX-based inference on Apple Silicon systems.
"""

import logging
from typing import Optional

import mlx.core as mx

from .kv_cache_profiles import (
    V2_SPEED_PROFILE,
    V3_QUALITY_PROFILE,
    AttentionCacheType,
    CompressionProfile,
    ModelSizeClass,
    create_auto_profile,
)

logger = logging.getLogger(__name__)

# Try to import TurboQuant KV cache support
try:
    from turboquant_mlx.layers.polar_kv_cache import (
        TurboQuantKVCache,
        convert_cache_to_turboquant,
    )

    TURBOQUANT_KV_AVAILABLE = True
    logger.info("TurboQuant KV cache compression available")
except ImportError as e:
    logger.warning(f"turboquant_mlx not available - KV cache compression disabled: {e}")
    TURBOQUANT_KV_AVAILABLE = False
    TurboQuantKVCache = None
    convert_cache_to_turboquant = None


class KVCacheCompressionManager:
    """Manages KV cache compression profiles and cache conversion.

    This class handles:
    - Compression profile selection based on model size and weight quantization
    - Cache type detection and compatibility checking
    - Conversion of standard KVCache to TurboQuantKVCache
    - Fallback to uncompressed cache on errors
    """

    def __init__(self, config: dict):
        """Initialize with KV cache config from profiles.yaml.

        Args:
            config: Dict with keys: enabled, profile, default_bits,
                   default_group_size, fallback_on_error
        """
        self.enabled = config.get("enabled", False) and TURBOQUANT_KV_AVAILABLE
        if config.get("enabled", False) and not TURBOQUANT_KV_AVAILABLE:
            logger.warning(
                "KV cache compression was enabled but TurboQuant is not available"
            )

        self.default_profile_name = config.get("profile", "auto")
        self.default_bits = config.get("default_bits", 3)
        self.default_group_size = config.get("default_group_size", 64)
        self.fallback_on_error = config.get("fallback_on_error", True)

        self.current_profile: Optional[CompressionProfile] = None
        self.compression_active = False
        self._model_size_class: Optional[ModelSizeClass] = None
        self._weight_bits: Optional[int] = None

        logger.info(
            f"KVCacheCompressionManager initialized: enabled={self.enabled}, "
            f"profile={self.default_profile_name}, available={TURBOQUANT_KV_AVAILABLE}"
        )

    def select_profile(
        self, model_size_class: str, weight_bits: Optional[int] = None
    ) -> Optional[CompressionProfile]:
        """Select compression profile based on model size and weight quantization.

        Args:
            model_size_class: "20B", "70B", "100B+"
            weight_bits: 3, 4, or None (FP16)

        Returns:
            CompressionProfile with appropriate bits and path, or None if disabled
        """
        if not self.enabled:
            return None

        if self.default_profile_name == "auto":
            return self._select_auto_profile(model_size_class, weight_bits)
        elif self.default_profile_name == "v2-speed":
            return V2_SPEED_PROFILE
        elif self.default_profile_name == "v3-quality":
            return V3_QUALITY_PROFILE
        else:
            # Custom profile - would load from kv_cache_profiles.yaml
            logger.warning(f"Unknown profile '{self.default_profile_name}', using auto")
            return self._select_auto_profile(model_size_class, weight_bits)

    def _select_auto_profile(
        self, model_size_class: str, weight_bits: Optional[int] = None
    ) -> CompressionProfile:
        """Apply double-compression rules for auto profile selection.

        Double-compression rules (from research):
        - 3-bit weights + 4-bit KV for ~20B models
        - 3-bit weights + 3-bit KV for 100B+ models
        - FP16 weights + 3-bit KV for any size (baseline)
        """
        try:
            size_class = ModelSizeClass(model_size_class)
        except ValueError:
            logger.warning(
                f"Unknown model size class: {model_size_class}, using 20B defaults"
            )
            size_class = ModelSizeClass.SIZE_20B

        # Create auto profile with appropriate bits
        profile = create_auto_profile()

        if weight_bits == 3:
            # Apply double-compression rules
            profile.bits = size_class.default_kv_bits
            logger.info(
                f"Auto profile: 3-bit weights + {profile.bits}-bit KV for {model_size_class}"
            )
        else:
            # FP16 weights or other - use default 3-bit KV
            profile.bits = self.default_bits
            logger.info(
                f"Auto profile: FP16/{weight_bits}-bit weights + {profile.bits}-bit KV"
            )

        # Select V2 for speed, V3 for quality (default to V2 for auto)
        profile.path = "v2"  # Speed-optimized by default
        profile.codebook_type = "uniform"

        return profile

    def detect_cache_type(self, cache_instance) -> AttentionCacheType:
        """Detect the type of attention cache.

        Args:
            cache_instance: An MLX attention cache instance

        Returns:
            AttentionCacheType enum value
        """
        cache_class_name = cache_instance.__class__.__name__

        if cache_class_name == "KVCache":
            return AttentionCacheType.KVCACHE
        elif cache_class_name == "RotatingKVCache":
            return AttentionCacheType.ROTATING_KV_CACHE
        elif cache_class_name == "ArraysCache":
            return AttentionCacheType.ARRAYS_CACHE
        else:
            logger.warning(
                f"Unknown cache type: {cache_class_name}, assuming uncompressible"
            )
            return AttentionCacheType.ARRAYS_CACHE  # Treat as uncompressible

    def convert_cache_to_turboquant(
        self, prompt_cache: list, profile: CompressionProfile
    ) -> list:
        """Convert prompt cache from KVCache to TurboQuantKVCache where applicable.

        Args:
            prompt_cache: List of (key_cache, value_cache) tuples per layer
            profile: CompressionProfile to apply

        Returns:
            Converted cache list with TurboQuantKVCache where applicable

        Note:
            - Only KVCache instances are compressed
            - RotatingKVCache and ArraysCache are returned unchanged
            - On error, falls back to uncompressed if fallback_on_error is True
        """
        if not self.enabled:
            logger.debug("KV cache compression disabled, returning original cache")
            return prompt_cache

        if not TURBOQUANT_KV_AVAILABLE:
            logger.warning("TurboQuant not available, returning original cache")
            return prompt_cache

        try:
            # Check if any cache needs compression
            has_kv_cache = False
            for k_cache, v_cache in prompt_cache:
                k_type = self.detect_cache_type(k_cache)
                if k_type == AttentionCacheType.KVCACHE:
                    has_kv_cache = True
                    break

            if not has_kv_cache:
                logger.info("No KVCache instances found, skipping compression")
                return prompt_cache

            # Convert the entire cache using TurboQuant
            logger.info(
                f"Converting cache to TurboQuant: bits={profile.bits}, "
                f"group_size={profile.group_size}, path={profile.path}"
            )

            converted_cache = convert_cache_to_turboquant(
                prompt_cache,
                tq_bits=profile.bits,
                group_size=profile.group_size,
                seed=42,
            )

            # Evaluate to materialize compressed data
            for c in converted_cache:
                if hasattr(c, "_tq_keys") and c._tq_keys is not None:
                    mx.eval(*c._tq_keys, *c._tq_values)

            self.current_profile = profile
            self.compression_active = True

            # Calculate memory savings
            original_bytes = sum(
                getattr(c, "nbytes", 0) for layer in prompt_cache for c in layer
            )
            compressed_bytes = sum(
                getattr(c, "nbytes", 0) for layer in converted_cache for c in layer
            )
            if original_bytes > 0:
                savings = original_bytes / max(compressed_bytes, 1)
                logger.info(
                    f"Cache conversion complete. Compression active: {self.compression_active}. "
                    f"Memory: {original_bytes / 1024 / 1024:.2f}MB → {compressed_bytes / 1024 / 1024:.2f}MB "
                    f"({savings:.1f}x savings)"
                )
            else:
                logger.info(
                    f"Cache conversion complete. Compression active: {self.compression_active}"
                )

            return converted_cache

        except Exception as e:
            logger.error(f"Cache conversion failed: {e}")
            if self.fallback_on_error:
                logger.warning("Falling back to uncompressed cache")
                self.compression_active = False
                return prompt_cache
            raise

    def get_status(self) -> dict:
        """Get current compression status for health endpoint.

        Returns:
            Dict with compression status information
        """
        return {
            "enabled": self.enabled,
            "available": TURBOQUANT_KV_AVAILABLE,
            "active": self.compression_active,
            "profile": self.current_profile.name if self.current_profile else None,
            "profile_path": self.current_profile.path if self.current_profile else None,
            "bits": self.current_profile.bits if self.current_profile else None,
            "model_size_class": self._model_size_class.value
            if self._model_size_class
            else None,
            "weight_bits": self._weight_bits,
            "fallback_on_error": self.fallback_on_error,
        }

    def enable(self, profile_name: Optional[str] = None) -> bool:
        """Enable compression with specified profile.

        Args:
            profile_name: Profile to use (overrides default)

        Returns:
            True if successfully enabled
        """
        if not TURBOQUANT_KV_AVAILABLE:
            logger.error("Cannot enable: TurboQuant KV cache not available")
            return False

        if profile_name:
            self.default_profile_name = profile_name

        self.enabled = True
        logger.info(
            f"KV cache compression enabled with profile: {self.default_profile_name}"
        )
        return True

    def disable(self):
        """Disable compression and revert to uncompressed cache."""
        self.enabled = False
        self.compression_active = False
        self.current_profile = None
        logger.info("KV cache compression disabled")

    def set_model_context(
        self, model_size_class: str, weight_bits: Optional[int] = None
    ):
        """Set model context for auto profile selection.

        Args:
            model_size_class: "20B", "70B", "100B+"
            weight_bits: Current weight quantization bits
        """
        try:
            self._model_size_class = ModelSizeClass(model_size_class)
        except ValueError:
            logger.warning(f"Invalid model size class: {model_size_class}")
            return

        self._weight_bits = weight_bits

        # Re-select profile if using auto
        if self.default_profile_name == "auto" and self.enabled:
            self.current_profile = self.select_profile(model_size_class, weight_bits)
            logger.info(f"Auto-selected profile: {self.current_profile.name}")
