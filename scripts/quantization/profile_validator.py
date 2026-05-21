"""
Profile validator for per-path hybrid quantization configurations.

Validates QuantizationProfile YAML files against schema requirements,
including bit-width ranges, group sizes, and calibration methods.
"""

import re
from dataclasses import dataclass
from typing import List, Optional

import yaml


class ProfileValidationError(Exception):
    """Raised when quantization profile validation fails."""

    def __init__(self, error_code: str, message: str, field: Optional[str] = None):
        self.error_code = error_code
        self.message = message
        self.field = field
        super().__init__(f"[{error_code}] {message}")


@dataclass
class QuantizationProfile:
    """Represents a per-path hybrid quantization configuration."""

    version: str
    preset_name: Optional[str]
    attention_bits: int
    expert_bits: int
    group_size: int
    calibration_method: str
    model_patterns: List[str]
    calibration_data_path: Optional[str] = None

    # Valid bit-width range
    MIN_BITS = 2
    MAX_BITS = 8

    # Valid group sizes
    VALID_GROUP_SIZES = [16, 32, 64, 128]

    # Valid calibration methods
    VALID_CALIBRATION_METHODS = ["none", "lloyd-max"]

    def validate(self) -> None:
        """
        Validate the quantization profile against schema requirements.

        Raises:
            ProfileValidationError: If validation fails with specific error code
        """
        # ERR-001: Bit-width validation
        if not (self.MIN_BITS <= self.attention_bits <= self.MAX_BITS):
            raise ProfileValidationError(
                "ERR-001",
                f"Attention bits must be between {self.MIN_BITS} and {self.MAX_BITS}, got {self.attention_bits}",
                "attention_bits",
            )

        if not (self.MIN_BITS <= self.expert_bits <= self.MAX_BITS):
            raise ProfileValidationError(
                "ERR-001",
                f"Expert bits must be between {self.MIN_BITS} and {self.MAX_BITS}, got {self.expert_bits}",
                "expert_bits",
            )

        # ERR-006: Group size validation
        if self.group_size not in self.VALID_GROUP_SIZES:
            raise ProfileValidationError(
                "ERR-006",
                f"Group size must be one of {self.VALID_GROUP_SIZES}, got {self.group_size}",
                "group_size",
            )

        # Calibration method validation
        if self.calibration_method not in self.VALID_CALIBRATION_METHODS:
            raise ProfileValidationError(
                "ERR-001",
                f"Calibration method must be one of {self.VALID_CALIBRATION_METHODS}, got {self.calibration_method}",
                "calibration_method",
            )

        # Model patterns validation
        if not self.model_patterns:
            raise ProfileValidationError(
                "ERR-001", "At least one model pattern is required", "model_patterns"
            )

        # Validate regex patterns
        for i, pattern in enumerate(self.model_patterns):
            try:
                re.compile(pattern)
            except re.error as e:
                raise ProfileValidationError(
                    "ERR-001",
                    f"Invalid regex pattern at index {i}: {pattern} - {str(e)}",
                    "model_patterns",
                )

        # Validate calibration data path if method is lloyd-max
        if self.calibration_method == "lloyd-max" and not self.calibration_data_path:
            raise ProfileValidationError(
                "ERR-003",
                "Calibration data path is required when using lloyd-max method",
                "calibration_data_path",
            )


class ProfileValidator:
    """Validates quantization profiles from YAML files or dictionaries."""

    @staticmethod
    def from_yaml_file(file_path: str) -> QuantizationProfile:
        """
        Load and validate a quantization profile from a YAML file.

        Args:
            file_path: Path to the YAML file

        Returns:
            Validated QuantizationProfile instance

        Raises:
            ProfileValidationError: If file cannot be read or validation fails
        """
        try:
            with open(file_path, "r") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            raise ProfileValidationError(
                "ERR-001", f"Failed to read YAML file: {str(e)}"
            )

        return ProfileValidator.from_dict(data, file_path)

    @staticmethod
    def from_dict(data: dict, source: Optional[str] = None) -> QuantizationProfile:
        """
        Validate a quantization profile from a dictionary.

        Args:
            data: Dictionary containing profile data
            source: Optional source identifier for error messages

        Returns:
            Validated QuantizationProfile instance

        Raises:
            ProfileValidationError: If validation fails
        """
        # Handle both nested and flat structures
        if "quantization_profiles" in data:
            # Nested structure (from profiles.yaml)
            profiles = data["quantization_profiles"]
            if not profiles:
                raise ProfileValidationError(
                    "ERR-001", "No quantization profiles found"
                )
            # Get first profile (or specify which one)
            profile_name = list(profiles.keys())[0]
            profile_data = profiles[profile_name]
        else:
            # Flat structure (direct profile)
            profile_data = data

        # Extract required fields with defaults
        try:
            profile = QuantizationProfile(
                version=profile_data.get("version", "1.0.0"),
                preset_name=profile_data.get("preset_name"),
                attention_bits=profile_data["attention_bits"],
                expert_bits=profile_data["expert_bits"],
                group_size=profile_data["group_size"],
                calibration_method=profile_data.get("calibration_method", "none"),
                model_patterns=profile_data.get("model_patterns", []),
                calibration_data_path=profile_data.get("calibration_data_path"),
            )
        except KeyError as e:
            raise ProfileValidationError("ERR-001", f"Missing required field: {str(e)}")

        # Validate the profile
        profile.validate()

        return profile

    @staticmethod
    def validate_calibration_path(path: str) -> bool:
        """
        Validate calibration data file path (T032, NFR-002).
        
        Args:
            path: Path to calibration data file
            
        Returns:
            True if path is valid
            
        Raises:
            ProfileValidationError: If path is invalid or insecure
        """
        import os
        
        # Check for path traversal attempts
        normalized_path = os.path.normpath(path)
        if ".." in normalized_path or normalized_path.startswith("/"):
            raise ProfileValidationError(
                "ERR-003",
                "Invalid calibration path: potential path traversal detected"
            )
        
        # Check if file exists
        if not os.path.exists(path):
            raise ProfileValidationError(
                "ERR-003",
                f"Calibration data file not found: {path}"
            )
        
        # Check file extension
        valid_extensions = ['.json', '.npy', '.txt', '.text']
        if not any(path.lower().endswith(ext) for ext in valid_extensions):
            raise ProfileValidationError(
                "ERR-003",
                f"Invalid calibration file format. Use: {valid_extensions}"
            )
        
        return True

    @staticmethod
    def validate_preset_name(preset_name: str) -> QuantizationProfile:
        """
        Validate a preset by name from profiles.yaml.

        Args:
            preset_name: Name of the preset (e.g., "tq3a-tq2e-g32")

        Returns:
            Validated QuantizationProfile instance

        Raises:
            ProfileValidationError: If preset not found or validation fails
        """
        import os

        # Load profiles.yaml
        profiles_path = os.path.join(
            os.path.dirname(__file__), "..", "wrapper-config", "profiles.yaml"
        )

        try:
            with open(profiles_path, "r") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            raise ProfileValidationError(
                "ERR-001", f"Failed to load profiles.yaml: {str(e)}"
            )

        # Find preset
        quantization_profiles = data.get("quantization_profiles", {})
        if preset_name not in quantization_profiles:
            available = list(quantization_profiles.keys())
            raise ProfileValidationError(
                "ERR-001",
                f"Preset '{preset_name}' not found. Available presets: {available}",
            )

        # Create profile dict with preset name
        profile_data = quantization_profiles[preset_name].copy()
        profile_data["preset_name"] = preset_name

        return ProfileValidator.from_dict(profile_data, f"preset:{preset_name}")
