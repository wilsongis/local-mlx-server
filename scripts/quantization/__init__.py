"""
Quantization module for per-path hybrid quantization support.

This module provides infrastructure for configuring and applying per-path
hybrid quantization to MLX models on Apple Silicon, including support for
latent-MoE architectures and Lloyd-Max codebook calibration.
"""

from .profile_validator import QuantizationProfile, ProfileValidationError
from .model_detector import ModelArchitecture, ModelDetectionError
from .config_builder import QuantizationConfigBuilder
from .quantization_manager import QuantizationManager

__version__ = "1.0.0"

__all__ = [
    "QuantizationProfile",
    "ProfileValidationError",
    "ModelArchitecture",
    "ModelDetectionError",
    "QuantizationConfigBuilder",
    "QuantizationManager",
]
