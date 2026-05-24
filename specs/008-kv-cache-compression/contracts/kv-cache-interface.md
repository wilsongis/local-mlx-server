# Contract: KV Cache Compression Interface

## Overview

This contract defines the interface for KV cache compression operations in the local MLX server. It specifies how compression profiles are configured, how cache conversion is triggered, and how the system reports compression status through the health endpoint.

## Configuration Contract

### Extension to profiles.yaml Schema

```yaml
# In scripts/wrapper-config/profiles.yaml
models:
  - name: "gpt-oss-120b"
    pattern: ".*gpt-oss.*120b.*"
    quantization:  # From spec 007
      attention_bits: 3
      expert_bits: 2
      group_size: 32
    kv_cache:  # NEW: KV cache compression configuration
      enabled: true
      profile: "auto"  # "v2-speed" | "v3-quality" | "auto"
      default_bits: 3
      default_group_size: 64
      fallback_on_error: true
```

### Compression Profile Definition

```yaml
# In scripts/wrapper-config/kv-cache-profiles.yaml (optional, for named profiles)
kv_cache_profiles:
  v2-speed:
    path: "v2"
    bits: 3
    group_size: 64
    use_metal: true
    hadamard_rotation: true
    codebook_type: "uniform"
    target_model_size: "any"
    
  v3-quality:
    path: "v3"
    bits: 3
    group_size: 64
    use_metal: true  # with CPU fallback
    hadamard_rotation: true
    codebook_type: "lloyd-max"
    target_model_size: "any"
    
  auto:
    path: "auto"  # Selects based on model size
    # Rules applied at runtime:
    # - 20B + 3-bit weights → 4-bit KV
    # - 100B+ + 3-bit weights → 3-bit KV
    # - FP16 weights → 3-bit KV (any size)
```

## Python API Contract

### KVCacheCompressionManager

```python
# scripts/quantization/kv_cache_compression.py

class KVCacheCompressionManager:
    """Manages KV cache compression profiles and cache conversion."""
    
    def __init__(self, config: dict):
        """
        Initialize with KV cache config from profiles.yaml.
        
        Args:
            config: Dict with keys: enabled, profile, default_bits, 
                   default_group_size, fallback_on_error
        """
        ...
    
    def select_profile(self, model_size_class: str, weight_bits: int) -> CompressionProfile:
        """
        Select compression profile based on model size and weight quantization.
        
        Args:
            model_size_class: "20B", "70B", "100B+"
            weight_bits: 3, 4, or None (FP16)
            
        Returns:
            CompressionProfile with appropriate bits and path
            
        Rules:
        - "auto" profile: Apply double-compression rules from research
        - "v2-speed" / "v3-quality": Use specified profile directly
        """
        ...
    
    def convert_cache(self, prompt_cache: list, profile: CompressionProfile) -> list:
        """
        Convert prompt cache from KVCache to TurboQuantKVCache where applicable.
        
        Args:
            prompt_cache: List of cache objects from mlx_lm.models.cache
            profile: CompressionProfile to apply
            
        Returns:
            New cache list with KVCache instances converted, others unchanged
            
        Behavior:
        - Detects KVCache vs RotatingKVCache vs ArraysCache
        - Only converts KVCache instances (growing caches)
        - Preserves existing cache state (offset, shape, dtype)
        - Handles attention sinks by returning float16 for standard SDPA path
        """
        ...
    
    def get_status(self) -> dict:
        """
        Return current compression status for health endpoint.
        
        Returns:
            {
                "kv_cache_compression": {
                    "enabled": bool,
                    "profile": str,  # "v2-speed", "v3-quality", "auto", "none"
                    "bits": int,
                    "group_size": int,
                    "path": str,  # "v2", "v3", "none"
                    "metal_accelerated": bool,
                    "compatible_caches": ["KVCache"],
                    "skipped_caches": ["RotatingKVCache", "ArraysCache"]
                }
            }
        """
        ...
```

### Cache Conversion Function

```python
# scripts/quantization/kv_cache_compression.py

def convert_cache_to_turboquant(
    prompt_cache: list,
    tq_bits: int = 3,
    group_size: int = 64,
    use_metal: bool = True,
    codebook_type: str = "lloyd-max"
) -> list:
    """
    Convert MLX prompt cache to TurboQuant compressed format.
    
    Args:
        prompt_cache: List of cache objects from model
        tq_bits: Bit-width for compression (2, 3, or 4)
        group_size: Elements per normalization group
        use_metal: Whether to use Metal acceleration (V2) or kernels (V3)
        codebook_type: "uniform" (V2) or "lloyd-max" (V3)
        
    Returns:
        New cache list with KVCache converted to TurboQuantKVCache
        
    Raises:
        ValueError: If bits not in [2, 3, 4] or group_size invalid
        RuntimeError: If Metal kernels fail to load (and use_metal=True)
        
    Fallback Behavior:
        - If use_metal=True and Metal fails: retry with use_metal=False
        - If codebook_type="lloyd-max" and no precomputed codebook: compute from data
        - If conversion fails for a layer: keep original KVCache, log warning
    """
    ...
```

## CLI / Just Recipe Contract

### Just Recipes

```makefile
# In justfile

# KV cache compression commands
kv-status:
    @python -m scripts.quantization.kv_cache_compression --status

kv-enable PROFILE="auto" BITS=3:
    @echo "Enabling KV cache compression: profile={{PROFILE}}, bits={{BITS}}"
    @python -m scripts.quantization.kv_cache_compression --enable --profile {{PROFILE}} --bits {{BITS}}

kv-disable:
    @echo "Disabling KV cache compression"
    @python -m scripts.quantization.kv_cache_compression --disable

kv-compress-model MODEL="":
    @echo "Testing KV cache compression on model: {{MODEL}}"
    @python -m scripts.quantization.kv_cache_compression --test-model {{MODEL}} --compare
```

### Environment Variables

```bash
# Optional overrides for compression settings
MLX_KV_CACHE_PROFILE="auto"       # Override profile selection
MLX_KV_CACHE_BITS=3               # Override bit-width
MLX_KV_CACHE_ENABLED=true          # Enable/disable compression
MLX_KV_CACHE_FALLBACK=true         # Enable fallback on error
```

## Health Endpoint Contract

### Extension to /health Response

```json
{
    "status": "healthy",
    "model": "gpt-oss-120b",
    "quantization": {
        "enabled": true,
        "profile": "tq3a-tq2e-g32",
        "attention_bits": 3,
        "expert_bits": 2
    },
    "kv_cache_compression": {
        "enabled": true,
        "profile": "auto",
        "resolved_profile": "v3-quality",
        "bits": 3,
        "group_size": 64,
        "path": "v3",
        "metal_accelerated": true,
        "compression_ratio": 4.6,
        "compatible_caches": ["KVCache"],
        "skipped_caches": ["RotatingKVCache", "ArraysCache"]
    }
}
```

**Field Descriptions**:
- `profile`: The configured profile ("v2-speed", "v3-quality", "auto")
- `resolved_profile`: The actual profile after auto-selection
- `compression_ratio`: Expected compression vs FP16 (e.g., 4.6x for 3-bit)
- `compatible_caches`: Cache types that will be compressed
- `skipped_caches`: Cache types that will be left uncompressed

## Integration Points

### With mlx_lm.server

```python
# In scripts/server-lifecycle.py or mlx_wrapper.py

def start_server_with_kv_compression(model, tokenizer, kv_config):
    """
    Start mlx_lm.server with KV cache compression enabled.
    
    Flow:
    1. Load model (potentially with weight quantization from spec 007)
    2. Process prompt with standard KVCache (full precision)
    3. Convert cache to TurboQuant format using convert_cache_to_turboquant()
    4. Continue generation with compressed cache
    """
    ...
```

### With Spec 007 QuantizationManager

```python
# Integration example
from scripts.quantization.quantization_manager import QuantizationManager
from scripts.quantization.kv_cache_compression import KVCacheCompressionManager

# Initialize both managers
quant_mgr = QuantizationManager(model_config)
kv_mgr = KVCacheCompressionManager(kv_config)

# Apply weight quantization (spec 007)
model = quant_mgr.apply_quantization(model)

# After prompt processing, apply KV compression (spec 008)
cache = kv_mgr.convert_cache(cache, profile)
```

## Error Handling Contract

| Error Condition | Behavior | Fallback |
|----------------|----------|----------|
| Metal kernels fail to load | Retry with CPU path (if V3) | CPU implementation |
| Invalid bit-width specified | Raise `ValueError` with valid options | Use default (3-bit) |
| Model size detection fails | Use "auto" with 3-bit default | Conservative 3-bit |
| Cache type detection fails | Skip compression for that layer | Keep original KVCache |
| Double-compression noise too high | Log warning, suggest 4-bit KV | Switch to 4-bit |
| Conversion fails mid-process | Restore original cache, disable compression | Uncompressed mode |

## Testing Contract

```python
# tests/test_kv_cache_compression.py

def test_v2_speed_compression():
    """Verify V2 path achieves ≥3x compression at ≥100% FP16 speed."""
    ...

def test_v3_quality_compression():
    """Verify V3 path achieves ≥4x compression within 2% quality."""
    ...

def test_hybrid_cache_compatibility():
    """Verify KVCache compressed, RotatingKVCache/ArraysCache skipped."""
    ...

def test_double_compression_20b():
    """Verify 3-bit weights + 4-bit KV works on ~20B model."""
    ...

def test_double_compression_120b():
    """Verify 3-bit weights + 3-bit KV works on 100B+ model."""
    ...

def test_mode_switching():
    """Verify compression mode switch completes in <5 seconds."""
    ...

def test_fallback_on_error():
    """Verify fallback to uncompressed on initialization failure."""
    ...
```
