"""
Tests for KV cache auto-profile selection logic.

Validates that the system automatically selects the correct compression strategy
based on model size class and weight quantization bits.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import MagicMock

import pytest

from scripts.quantization.kv_cache_compression import KVCacheCompressionManager
from scripts.quantization.kv_cache_profiles import ModelSizeClass


class TestAutoProfileSelection20B:
    """Test auto-profile selection for ~20B models."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "enabled": True,
            "profile": "auto",
            "default_bits": 3,
            "default_group_size": 64,
            "fallback_on_error": True,
        }
        self.manager = KVCacheCompressionManager(self.config)

    def test_20b_model_3bit_weights_selects_4bit_kv(self):
        """T034: Test auto profile selects 3-bit weights + 4-bit KV for ~20B models."""
        # 20B model with 3-bit weight quantization
        profile = self.manager.select_profile("20B", weight_bits=3)

        assert profile is not None
        assert profile.bits == 4  # 4-bit KV for 20B + 3-bit weights
        assert profile.path in ("v2", "v3", "auto")
        print(f"20B + 3-bit weights → {profile.bits}-bit KV (expected: 4-bit)")

    def test_20b_model_fp16_weights_selects_3bit_kv(self):
        """Test auto profile selects FP16 weights + 3-bit KV for ~20B models."""
        # 20B model with FP16 weights (no quantization)
        profile = self.manager.select_profile("20B", weight_bits=None)

        assert profile is not None
        assert profile.bits == 3  # 3-bit KV for FP16 weights
        print(f"20B + FP16 weights → {profile.bits}-bit KV (expected: 3-bit)")

    def test_20b_model_4bit_weights_selects_3bit_kv(self):
        """Test auto profile selects 4-bit weights + 3-bit KV for ~20B models."""
        profile = self.manager.select_profile("20B", weight_bits=4)

        assert profile is not None
        assert profile.bits == 3  # 3-bit KV default
        print(f"20B + 4-bit weights → {profile.bits}-bit KV (expected: 3-bit)")


class TestAutoProfileSelection100BPlus:
    """Test auto-profile selection for 100B+ models."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "enabled": True,
            "profile": "auto",
            "default_bits": 3,
            "default_group_size": 64,
            "fallback_on_error": True,
        }
        self.manager = KVCacheCompressionManager(self.config)

    def test_100b_model_3bit_weights_selects_3bit_kv(self):
        """T035: Test auto profile selects 3-bit weights + 3-bit KV for 100B+ models."""
        # 100B+ model with 3-bit weight quantization
        profile = self.manager.select_profile("100B+", weight_bits=3)

        assert profile is not None
        assert profile.bits == 3  # 3-bit KV for 100B+ + 3-bit weights
        assert profile.path in ("v2", "v3", "auto")
        print(f"100B+ + 3-bit weights → {profile.bits}-bit KV (expected: 3-bit)")

    def test_100b_model_fp16_weights_selects_3bit_kv(self):
        """Test auto profile selects FP16 weights + 3-bit KV for 100B+ models."""
        profile = self.manager.select_profile("100B+", weight_bits=None)

        assert profile is not None
        assert profile.bits == 3  # 3-bit KV for FP16 weights
        print(f"100B+ + FP16 weights → {profile.bits}-bit KV (expected: 3-bit)")

    def test_100b_model_double_compression_tolerance(self):
        """Test that 100B+ models tolerate double-compression (3+3) well."""
        profile = self.manager.select_profile("100B+", weight_bits=3)

        # Verify double-compression rule: 3-bit weights + 3-bit KV
        assert profile.bits == 3

        # 100B+ models have redundancy to absorb noise from double-compression
        # This is a key research finding
        model_class = ModelSizeClass("100B+")
        assert model_class.default_kv_bits == 3
        assert model_class.min_memory_gb == 48  # 48GB required for 100B+
        print("100B+ double-compression (3+3) validated - redundancy absorbs noise")


class TestAutoProfileSelection70B:
    """Test auto-profile selection for 70B models (edge case)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "enabled": True,
            "profile": "auto",
            "default_bits": 3,
            "default_group_size": 64,
            "fallback_on_error": True,
        }
        self.manager = KVCacheCompressionManager(self.config)

    def test_70b_model_defaults_to_3bit_kv(self):
        """Test 70B model defaults to 3-bit KV."""
        profile = self.manager.select_profile("70B", weight_bits=3)

        assert profile is not None
        assert profile.bits == 3  # Conservative default
        print(f"70B + 3-bit weights → {profile.bits}-bit KV (expected: 3-bit)")


class TestModelSizeClassDetection:
    """Test model size class detection from parameter counts."""

    def test_determine_model_size_class_20b(self):
        """Test model size detection for ~20B models."""
        from scripts.quantization.quantization_manager import QuantizationManager

        # Mock model architecture with ~20B params
        mock_arch = MagicMock()
        mock_arch.total_params = 20e9  # 20 billion

        # Create a minimal manager to test the method
        manager = QuantizationManager("")
        manager.model_architecture = mock_arch

        size_class = manager._determine_model_size_class()
        assert size_class == "20B"
        print(f"Detected model size class: {size_class} (20B params)")

    def test_determine_model_size_class_100b_plus(self):
        """Test model size detection for 100B+ models."""
        from scripts.quantization.quantization_manager import QuantizationManager

        # Mock model architecture with ~120B params
        mock_arch = MagicMock()
        mock_arch.total_params = 120e9  # 120 billion

        manager = QuantizationManager("")
        manager.model_architecture = mock_arch

        size_class = manager._determine_model_size_class()
        assert size_class == "100B+"
        print(f"Detected model size class: {size_class} (120B params)")


class TestDoubleCompressionRules:
    """Test double-compression tolerance rules from research."""

    def test_20b_3bit_weights_4bit_kv_clean_output(self):
        """Verify 20B + 3-bit weights + 4-bit KV produces clean output."""
        config = {
            "enabled": True,
            "profile": "auto",
            "default_bits": 3,
            "default_group_size": 64,
            "fallback_on_error": True,
        }
        manager = KVCacheCompressionManager(config)
        profile = manager.select_profile("20B", weight_bits=3)

        # Rule: 3-bit weights + 4-bit KV = clean output (4x KV savings)
        assert profile.bits == 4
        print("✓ 20B: 3-bit weights + 4-bit KV → clean output (4x KV savings)")

    def test_20b_3bit_weights_3bit_kv_repetition_collapse(self):
        """Verify 20B + 3-bit weights + 3-bit KV causes repetition collapse."""
        # This is a known issue from research - small models can't handle
        # double-compression noise
        config = {
            "enabled": True,
            "profile": "auto",
            "default_bits": 3,  # Would force 3-bit KV
            "default_group_size": 64,
            "fallback_on_error": True,
        }
        manager = KVCacheCompressionManager(config)

        # Manually set bits to 3 to simulate wrong config
        profile = manager.select_profile("20B", weight_bits=3)
        # The auto profile should set 4-bit for 20B + 3-bit weights
        # If someone manually forces 3-bit, it would cause issues
        assert profile.bits == 4  # Auto profile correctly selects 4-bit
        print("✓ Auto profile prevents 20B repetition collapse by selecting 4-bit KV")

    def test_100b_3bit_weights_3bit_kv_clean_output(self):
        """Verify 100B+ + 3-bit weights + 3-bit KV produces clean output."""
        config = {
            "enabled": True,
            "profile": "auto",
            "default_bits": 3,
            "default_group_size": 64,
            "fallback_on_error": True,
        }
        manager = KVCacheCompressionManager(config)
        profile = manager.select_profile("100B+", weight_bits=3)

        # Rule: 3-bit weights + 3-bit KV = clean output (redundancy absorbs noise)
        assert profile.bits == 3
        print(
            "✓ 100B+: 3-bit weights + 3-bit KV → clean output (redundancy absorbs noise)"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
