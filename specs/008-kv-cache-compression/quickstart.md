# Quickstart: KV Cache Compression

## Prerequisites

- Apple Silicon Mac (M1/M2/M3/M4) with macOS 14+
- Xcode Command Line Tools installed (`xcode-select --install`)
- CMake 3.27+ installed (`brew install cmake`)
- Existing local-mlx-server setup (from spec 007 hybrid quantization)
- Python 3.11+ with `mlx` and `mlx-lm` installed via `uv`

## Installation

### Option 1: Use turboquant-mlx Package (Recommended)

```bash
# Install TurboQuant MLX with Metal kernel support
uv pip install turboquant-mlx-full
```

This installs the pre-built package with Metal kernels. The package provides:
- V2 speed-optimized path (Metal-accelerated)
- V3 quality-optimized path (Lloyd-Max codebook)
- `convert_cache_to_turboquant()` function
- Demo scripts for testing

### Option 2: Build from Source (For Development)

```bash
# Clone the reference implementation
git clone https://github.com/manjunathshiva/turboquant-mlx.git
cd turboquant-mlx

# Install in development mode (compiles Metal kernels)
uv pip install -e .
```

## Quick Test: KV Cache Compression on Any Model

### Basic Test (FP16 Weights + Compressed KV)

```bash
# Test with GPT-OSS-20B (or any MLX-compatible model)
python -m turboquant_mlx.demo_kv \
  --model openai/gpt-oss-20b \
  --prompt "Why is the sky blue?" \
  --max-tokens 200 \
  --tq-bits 3 \
  --compare
```

This runs FP16 and TurboQuant 3-bit KV cache side-by-side, showing:
- Tokens/second for each configuration
- KV cache memory usage (FP16 vs compressed)
- Output quality comparison

Expected output:
```
FP16:        90.6 tok/s, KV cache: 2.1 MB
TurboQuant:  29.9 tok/s, KV cache: 0.6 MB (3.5x smaller)
```

### Test with Compressed Weights + Compressed KV (Double Compression)

```bash
# First, convert model weights to 3-bit (from spec 007)
turboquant-convert --hf-path openai/gpt-oss-120b --bits 3 --mlx-path gpt-oss-120b-tq3

# Then test with KV compression (use 4-bit KV for 20B, 3-bit for 120B+)
python -m turboquant_mlx.demo_kv \
  --model gpt-oss-120b-tq3 \
  --prompt "Explain quantum computing" \
  --max-tokens 500 \
  --tq-bits 3  # Use 3-bit for 120B+, 4-bit for ~20B
```

## Integration with Local MLX Server

### Step 1: Enable KV Cache Compression in profiles.yaml

Edit `scripts/wrapper-config/profiles.yaml`:

```yaml
models:
  - name: "gpt-oss-120b"
    pattern: ".*gpt-oss.*120b.*"
    quantization:  # From spec 007
      attention_bits: 3
      expert_bits: 2
      group_size: 32
    kv_cache:  # NEW: KV cache compression
      enabled: true
      profile: "auto"  # "v2-speed" | "v3-quality" | "auto"
      default_bits: 3
      default_group_size: 64
      fallback_on_error: true
```

### Step 2: Use Just Recipes for Operations

```bash
# Check current KV cache compression status
just kv-status

# Enable compression with auto profile (recommended)
just kv-enable auto 3

# Enable speed-optimized path (V2)
just kv-enable v2-speed 3

# Enable quality-optimized path (V3)
just kv-enable v3-quality 3

# Disable compression
just kv-disable

# Test compression on a specific model
just kv-compress-model openai/gpt-oss-20b
```

### Step 3: Start Server with Compression

```bash
# Start server (compression auto-applied based on profiles.yaml)
just up

# Or with environment variable override:
MLX_KV_CACHE_PROFILE=v2-speed just up
```

The server will:
1. Load model with weight quantization (if configured in spec 007)
2. Process prompt with full-precision KV cache
3. Convert cache to TurboQuant format after prompt processing
4. Continue generation with compressed KV cache

## Verify Compression is Working

### Check Health Endpoint

```bash
# Query health endpoint
curl http://localhost:8080/health | jq '.kv_cache_compression'

# Expected output:
{
  "enabled": true,
  "profile": "auto",
  "resolved_profile": "v3-quality",
  "bits": 3,
  "compression_ratio": 4.6,
  "metal_accelerated": true
}
```

### Monitor Memory Usage

```bash
# During generation, watch memory usage
# Before compression: ~48 GB (120B model + KV cache)
# After compression: ~40-42 GB (7-8 GB saved on KV cache)
```

## Compression Strategy Rules (Auto Profile)

The "auto" profile automatically selects the right configuration:

| Model Size | Weight Bits | Recommended KV Bits | Reason |
|------------|-------------|---------------------|--------|
| ~20B | 3 (compressed) | **4-bit** | Avoid compounding noise |
| ~20B | FP16 | 3-bit | Safe, good compression |
| 100B+ | 3 (compressed) | **3-bit** | Redundancy absorbs noise |
| 100B+ | FP16 | 3-bit | Maximum compression |

**Key Finding**: 120B+ models tolerate aggressive double-compression (3+3) and actually run *faster* due to reduced memory bandwidth.

## Troubleshooting

### Metal Kernels Fail to Load

```bash
# Check Xcode tools and CMake
xcode-select -p
cmake --version

# Reinstall with verbose output
uv pip install --force-reinstall turboquant-mlx-full -v

# Fallback to CPU (slower but works)
just kv-enable v3-quality 3  # Will auto-fallback if Metal fails
```

### Output Quality Degradation (Repetition/Drift)

**Cause**: Double-compression noise on small models

**Fix**: Use 4-bit KV with 3-bit weights for ~20B models:
```yaml
kv_cache:
  profile: "v3-quality"
  default_bits: 4  # Use 4-bit for small models
```

### Attention Sinks Error (GPT-OSS)

**Symptom**: `ValueError: Quantized SDPA does not support attention sinks`

**Cause**: Using quantized attention path instead of standard path

**Fix**: Already handled by our implementation (returns float16, uses standard SDPA)

### Memory Still Insufficient

**Try**: Combine with spec 007 weight compression:
```bash
# 3-bit weights + 3-bit KV = ~20B parameter model in ~7GB, KV cache 4x smaller
# Enables 120B+ models on 48GB systems with extended context
```

## Next Steps

1. Read the [research.md](research.md) for detailed implementation decisions
2. Review [data-model.md](data-model.md) for entity definitions
3. Check [contracts/kv-cache-interface.md](contracts/kv-cache-interface.md) for API details
4. See [plan.md](plan.md) for full implementation plan
5. Run `/speckit.tasks` to generate implementation task list

## Performance Expectations

### GPT-OSS-20B (64GB M4 Max)
| Config | Tok/s | KV Cache | Notes |
|--------|-------|----------|-------|
| FP16 | 90.6 | 2.1 MB @ 872 tokens | Baseline |
| TQ 3-bit KV | 29.9 | 0.6 MB (3.5x smaller) | Slower (small model) |
| TQ 3-bit weights + 4-bit KV | ~85 | 0.8 MB | Double compression |

### GPT-OSS-120B (64GB M4 Max)
| Config | Tok/s | KV Cache @ 131K | Notes |
|--------|-------|-----------------|-------|
| FP16 weights, no KV compression | 6.4 | 9.2 GB | Doesn't fit at full context |
| TQ 3-bit weights + TQ 3-bit KV | 8.7 | 1.8 GB (7.4 GB saved) | **Fits at 131K context!** |

**Key Insight**: On large models (120B+), compression is *faster* than FP16 due to reduced memory bandwidth.
