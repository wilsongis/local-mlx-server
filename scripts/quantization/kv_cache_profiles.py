"""KV Cache Compression Profiles and Data Models.

This module defines the data structures for KV cache compression profiles,
model size classifications, and compression configuration.
"""

from dataclasses import dataclass
from enum import Enum


class ModelSizeClass(Enum):
    """Categorization of models used to determine optimal compression strategy."""

    SIZE_20B = "20B"
    SIZE_70B = "70B"
    SIZE_100B_PLUS = "100B+"

    @property
    def weight_bits(self) -> int:
        """Recommended weight quantization bits for double-compression."""
        return 3  # From spec 007

    @property
    def default_kv_bits(self) -> int:
        """Recommended KV cache bits based on double-compression rules."""
        if self == ModelSizeClass.SIZE_20B:
            return 4  # 3-bit weights + 4-bit KV
        elif self == ModelSizeClass.SIZE_100B_PLUS:
            return 3  # 3-bit weights + 3-bit KV
        return 3  # Conservative default

    @property
    def min_memory_gb(self) -> int:
        """Minimum system memory required."""
        if self == ModelSizeClass.SIZE_100B_PLUS:
            return 48  # 48GB for 100B+ with double-compression
        return 32


class AttentionCacheType(Enum):
    """Enumeration of MLX attention cache implementations."""

    KVCACHE = "KVCache"
    ROTATING_KV_CACHE = "RotatingKVCache"
    ARRAYS_CACHE = "ArraysCache"

    @property
    def is_compressible(self) -> bool:
        """Whether this cache type supports compression."""
        return self == AttentionCacheType.KVCACHE


@dataclass
class CompressionProfile:
    """A named configuration specifying compression path, bit-width, and kernel requirements."""

    name: str
    path: str  # "v2" (speed-optimized) or "v3" (quality-optimized)
    bits: int = 3
    group_size: int = 64
    use_metal: bool = True
    hadamard_rotation: bool = True
    codebook_type: str = "uniform"  # "uniform" (V2) or "lloyd-max" (V3)
    target_model_size: str = "any"

    def __post_init__(self):
        """Validate the profile configuration."""
        if self.path not in ("v2", "v3", "auto"):
            raise ValueError(
                f"Invalid path: {self.path}. Must be 'v2', 'v3', or 'auto'"
            )

        if self.bits not in (2, 3, 4):
            raise ValueError(f"Invalid bits: {self.bits}. Must be 2, 3, or 4")

        if self.group_size <= 0 or (self.group_size & (self.group_size - 1)) != 0:
            raise ValueError(f"group_size must be power of 2, got {self.group_size}")

        if self.codebook_type not in ("uniform", "lloyd-max"):
            raise ValueError(f"Invalid codebook_type: {self.codebook_type}")

    @property
    def is_v2(self) -> bool:
        """Check if this is a V2 (speed-optimized) profile."""
        return self.path == "v2"

    @property
    def is_v3(self) -> bool:
        """Check if this is a V3 (quality-optimized) profile."""
        return self.path == "v3"

    @property
    def expected_compression_ratio(self) -> float:
        """Estimated compression ratio based on bit-width (FP16 baseline)."""
        return 16.0 / self.bits

    def to_dict(self) -> dict:
        """Convert profile to dictionary for serialization."""
        return {
            "name": self.name,
            "path": self.path,
            "bits": self.bits,
            "group_size": self.group_size,
            "use_metal": self.use_metal,
            "hadamard_rotation": self.hadamard_rotation,
            "codebook_type": self.codebook_type,
            "target_model_size": self.target_model_size,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CompressionProfile":
        """Create profile from dictionary."""
        return cls(**data)


# Pre-defined profile templates
V2_SPEED_PROFILE = CompressionProfile(
    name="v2-speed",
    path="v2",
    bits=3,
    group_size=64,
    use_metal=True,
    hadamard_rotation=True,
    codebook_type="uniform",
    target_model_size="any",
)

V3_QUALITY_PROFILE = CompressionProfile(
    name="v3-quality",
    path="v3",
    bits=3,
    group_size=64,
    use_metal=True,
    hadamard_rotation=True,
    codebook_type="lloyd-max",
    target_model_size="any",
)


def create_auto_profile() -> CompressionProfile:
    """Create an auto-selection profile that chooses based on model size."""
    return CompressionProfile(
        name="auto",
        path="auto",
        bits=3,
        group_size=64,
        use_metal=True,
        hadamard_rotation=True,
        codebook_type="uniform",  # Will be determined at runtime
        target_model_size="any",
    )
