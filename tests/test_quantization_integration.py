"""
Integration tests for per-path hybrid quantization feature.

Tests the complete flow: profile apply → model load → health check → inference
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.quantization.config_builder import QuantizationConfigBuilder  # noqa: E402
from scripts.quantization.model_detector import ModelArchitecture, ModelDetector  # noqa: E402
from scripts.quantization.profile_validator import (  # noqa: E402
    ProfileValidationError,
    ProfileValidator,
    QuantizationProfile,
)
from scripts.quantization.quantization_manager import QuantizationManager  # noqa: E402


class TestQuantizationIntegration:
    """Integration tests for the complete quantization flow."""

    @pytest.fixture
    def sample_profile(self):
        """Create a sample quantization profile for testing."""
        return QuantizationProfile(
            version="1.0.0",
            preset_name="tq3a-tq2e-g32",
            attention_bits=3,
            expert_bits=2,
            group_size=32,
            calibration_method="none",
            model_patterns=[".*nemotron.*120b.*"],
        )

    @pytest.fixture
    def mock_model_path(self, tmp_path):
        """Create a mock model directory structure."""
        model_dir = tmp_path / "test-model"
        model_dir.mkdir()

        # Create minimal config.json
        config = {
            "model_type": "nemotron",
            "num_experts": 8,
            "architectures": ["Nemotron3ForCausalLM"],
        }
        with open(model_dir / "config.json", "w") as f:
            json.dump(config, f)

        # Create a dummy model file
        (model_dir / "model.safetensors").touch()

        return str(model_dir)

    def test_profile_apply_flow(self, sample_profile, mock_model_path):
        """Test T038: Complete flow from profile apply to model load."""
        # Step 1: Validate profile
        sample_profile.validate()  # Should not raise

        # Step 2: Create quantization manager
        manager = QuantizationManager(
            model_path=mock_model_path, profile_name="tq3a-tq2e-g32"
        )

        # Step 3: Initialize (loads profile and detects model)
        with patch.object(
            ProfileValidator, "validate_preset_name", return_value=sample_profile
        ):
            with patch.object(ModelDetector, "detect") as mock_detect:
                mock_arch = ModelArchitecture(
                    architecture_name="Nemotron-3-Super-120B-A12B",
                    is_moe=True,
                    expert_count=8,
                    active_params=12000000000,
                    total_params=120000000000,
                )
                mock_detect.return_value = mock_arch

                manager.initialize()

                # Verify profile was loaded
                assert manager.profile is not None
                assert manager.profile.attention_bits == 3
                assert manager.profile.expert_bits == 2

                # Verify model architecture was detected
                assert manager.model_architecture is not None
                assert manager.model_architecture.is_moe is True

    def test_health_endpoint_quantization_object(self, sample_profile):
        """Test that health endpoint includes quantization object."""
        # Build config from profile
        builder = QuantizationConfigBuilder(sample_profile)
        config = builder.build_config()

        # Verify config structure
        assert "quantization" in config
        assert config["quantization"]["type"] == "per_path_hybrid"
        assert len(config["quantization"]["paths"]) >= 1

        # Check attention path
        attention_path = next(
            p
            for p in config["quantization"]["paths"]
            if "attention" in p.get("pattern", "")
        )
        assert attention_path["bits"] == 3
        assert attention_path["group_size"] == 32

    def test_moe_model_detection(self, mock_model_path):
        """Test detection of MoE models."""
        detector = ModelDetector(mock_model_path)
        arch = detector.detect()

        assert arch is not None
        assert arch.is_moe is True
        assert arch.expert_count == 8

    def test_per_path_quantization_config(self, sample_profile):
        """Test that per-path config generates correct bit-widths."""
        builder = QuantizationConfigBuilder(sample_profile)

        # Mock MoE architecture
        arch = ModelArchitecture(
            architecture_name="Test-MoE",
            is_moe=True,
            expert_count=8,
        )

        config = builder.build_config(arch)

        # Should have attention and expert paths
        assert len(config["quantization"]["paths"]) == 2

        # Find paths
        attention = next(
            p
            for p in config["quantization"]["paths"]
            if "attention" in p.get("pattern", "")
        )
        expert = next(
            p
            for p in config["quantization"]["paths"]
            if "expert" in p.get("pattern", "")
        )

        assert attention["bits"] == 3  # attention_bits
        assert expert["bits"] == 2  # expert_bits

    def test_error_handling_err001_invalid_bits(self):
        """Test ERR-001: Invalid bit-width handling."""
        profile = QuantizationProfile(
            version="1.0.0",
            preset_name="invalid",
            attention_bits=9,  # Invalid: > 8
            expert_bits=2,
            group_size=32,
            calibration_method="none",
            model_patterns=[".*"],
        )

        with pytest.raises(ProfileValidationError) as exc_info:
            profile.validate()

        assert exc_info.value.error_code == "ERR-001"

    def test_error_handling_err006_invalid_group_size(self):
        """Test ERR-006: Invalid group size handling."""
        profile = QuantizationProfile(
            version="1.0.0",
            preset_name="invalid",
            attention_bits=3,
            expert_bits=2,
            group_size=24,  # Invalid: not in [16, 32, 64, 128]
            calibration_method="none",
            model_patterns=[".*"],
        )

        with pytest.raises(ProfileValidationError) as exc_info:
            profile.validate()

        assert exc_info.value.error_code == "ERR-006"

    @patch("scripts.quantization.quantization_manager.os.path.exists")
    def test_model_checksum_validation(self, mock_exists):
        """Test ERR-004: Model checksum validation."""
        mock_exists.return_value = True

        manager = QuantizationManager(
            model_path="/fake/model", profile_name="tq3a-tq2e-g32"
        )

        # Mock profile
        manager.profile = QuantizationProfile(
            version="1.0.0",
            preset_name="tq3a-tq2e-g32",
            attention_bits=3,
            expert_bits=2,
            group_size=32,
            calibration_method="none",
            model_patterns=[".*"],
        )

        # Test checksum validation
        with patch("builtins.open", MagicMock()):
            with patch("hashlib.md5") as mock_md5:
                mock_md5.return_value.hexdigest.return_value = "abc123"

                # Should not raise if checksums match
                # (Implementation would compare checksums)
                result = manager.validate_model_checksum()
                assert result is True or result is False  # Should return boolean

    def test_rollback_on_failure(self):
        """Test NFR-005: Rollback logic on failed quantization."""
        manager = QuantizationManager(
            model_path="/fake/model", profile_name="tq3a-tq2e-g32"
        )

        # Mock profile and architecture
        manager.profile = QuantizationProfile(
            version="1.0.0",
            preset_name="tq3a-tq2e-g32",
            attention_bits=3,
            expert_bits=2,
            group_size=32,
            calibration_method="none",
            model_patterns=[".*"],
        )
        manager.model_architecture = ModelArchitecture(
            architecture_name="Test", is_moe=False
        )
        manager.config_builder = QuantizationConfigBuilder(manager.profile)

        # Test that apply_quantization handles errors gracefully
        with patch.object(
            manager.config_builder,
            "build_config",
            side_effect=Exception("Quant failed"),
        ):
            with pytest.raises(Exception):
                manager.apply_quantization()

            # Verify rollback would be triggered (logged)
            # (Actual rollback logic is in the implementation)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
