# Quickstart: Per-Path Hybrid Quantization

## Overview
This guide walks you through configuring and using per-path hybrid quantization for MLX models on Apple Silicon. You'll learn to apply `tq3a-tq2e g32` presets, support latent-MoE architectures, and optionally use Lloyd-Max codebook calibration.

## Prerequisites
- Apple Silicon Mac (M-series) with 48GB+ unified memory recommended for 120B+ models
- MLX and mlx-lm installed (`uv pip install mlx-lm` or `pip install mlx-lm`)
- Local MLX Server repository cloned and `just` command available
- Nemotron-3-Super-120B-A12B or similar model downloaded

## Step 1: List Available Quantization Profiles

```bash
just quant-list
```

**Expected Output**:
```
Available Quantization Profiles:
  - tq3a-tq2e-g32 (attention: 3-bit, expert: 2-bit, group: 32)
  - tq4a-tq4e-g32 (attention: 4-bit, expert: 4-bit, group: 32)
```

## Step 2: Validate a Quantization Profile

Before applying, validate your profile syntax:

```bash
just quant-validate tq3a-tq2e-g32
```

Or validate a custom YAML file:
```bash
just quant-validate /path/to/custom-profile.yaml
```

**On Success**: Exit code 0, no output (silent success)
**On Failure**: Exit code 1, error message with line numbers (ERR-001, ERR-006)

## Step 3: Apply Quantization to a Model

Apply the `tq3a-tq2e-g32` profile to Nemotron-3-Super-120B-A12B:

```bash
just quant-apply ~/.cache/huggingface/hub/Nemotron-3-Super-120B-A12B tq3a-tq2e-g32
```

**What Happens**:
1. Profile validated
2. Model architecture detected (MoE with 8 experts)
3. Attention layers quantized to 3-bit, expert layers to 2-bit
4. Group size 32 applied
5. Model loaded with per-path quantization
6. `.active-model` updated with quantized model reference

**Expected Output**:
```
Applying quantization profile 'tq3a-tq2e-g32' to Nemotron-3-Super-120B-A12B...
✓ Model architecture detected: Nemotron-3-Super-120B-A12B (MoE, 8 experts)
✓ Attention layers: 3-bit quantization, group 32
✓ Expert layers: 2-bit quantization, group 32
✓ Model loaded successfully (estimated memory: 48.0 GB)
```

## Step 4: Check Quantization Status

View current quantization configuration:

```bash
just quant-status
```

**Expected Output**:
```
Active Model: Nemotron-3-Super-120B-A12B
Quantization Profile: tq3a-tq2e-g32
  - Attention layers: 3-bit, group 32
  - Expert layers: 2-bit, group 32
  - Calibration: none
Memory Estimate: 48.0 GB
```

## Step 5: Verify via Health Endpoint

Start the server (if not running) and check the extended health endpoint:

```bash
just mlx-start
curl http://localhost:8080/health
```

**Expected Response**:
```json
{
  "status": "ok",
  "model": "Nemotron-3-Super-120B-A12B",
  "quantization": {
    "profile": "tq3a-tq2e-g32",
    "attention_bits": 3,
    "expert_bits": 2,
    "group_size": 32,
    "calibration_method": "none",
    "model_architecture": "Nemotron-3-Super-120B-A12B",
    "is_moe": true,
    "expert_count": 8,
    "active_params": 12000000000,
    "total_params": 120000000000
  }
}
```

## Step 6: (Optional) Lloyd-Max Codebook Calibration

For improved quantization accuracy, use calibration data with Lloyd-Max optimization:

### 6a. Prepare Calibration Data

**JSON Format** (`calibration.json`):
```json
{
  "samples": [
    [101, 202, 345, 456, ...],
    [102, 203, 456, 567, ...]
  ]
}
```

**Text Format** (`calibration.txt`):
```
Sample conversation or text for calibration...
```

### 6b. Run Calibration

```bash
just quant-calibrate calibration.json scripts/wrapper-config/codebooks/nemotron-120b-lloyd-max
```

**Expected Output**:
```
Running Lloyd-Max calibration (V3 algorithm)...
✓ Loaded 1000 calibration samples
✓ Generated codebooks for 3-bit attention layers
✓ Generated codebooks for 2-bit expert layers
✓ Codebooks saved to scripts/wrapper-config/codebooks/
✓ Perplexity improvement: 12.5% vs standard quantization
```

### 6c. Apply Profile with Lloyd-Max

Update your profile to use Lloyd-Max:
```yaml
quantization_profiles:
  tq3a-tq2e-g32-lloyd:
    version: "1.0.0"
    attention_bits: 3
    expert_bits: 2
    group_size: 32
    calibration_method: "lloyd-max"
    model_patterns: [".*nemotron.*120b.*"]
```

Apply the updated profile:
```bash
just quant-apply ~/.cache/huggingface/hub/Nemotron-3-Super-120B-A12B tq3a-tq2e-g32-lloyd
```

## Step 7: Test Inference

Verify the quantized model works correctly:

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Nemotron-3-Super-120B-A12B",
    "messages": [{"role": "user", "content": "Explain quantum computing in one sentence."}]
  }'
```

**Expected**: Valid OpenAI-compatible response with generated text.

## Troubleshooting

### ERR-001: Invalid Bit-Width
```
Error: Invalid bit-width: 9. Must be between 2 and 8.
```
**Fix**: Use bit-widths between 2-8 in your profile.

### ERR-002: Unsupported Model Architecture
```
Error: Unsupported model architecture: unknown-model. Cannot identify layer types for per-path quantization.
```
**Fix**: Add model pattern to profile's `model_patterns` or manually specify layer types.

### ERR-003: Calibration Data Format Error
```
Error: Invalid calibration data format: csv. Supported formats: JSON, numpy, text.
```
**Fix**: Convert calibration data to supported format.

### ERR-005: Insufficient Memory
```
Error: Insufficient memory for quantization configuration. Required: 50GB, Available: 48GB.
```
**Fix**: Use lower bit-widths or smaller group size to reduce memory.

### ERR-006: Invalid Group Size
```
Error: Invalid group size: 24. Must be one of: 16, 32, 64, 128.
```
**Fix**: Use valid group size (16, 32, 64, or 128).

## Next Steps

- Read the full [Feature Specification](spec.md) for detailed requirements
- Review [Data Model](data-model.md) for entity relationships
- Check [Research](research.md) for design decisions and alternatives
- See [Implementation Plan](plan.md) for phased development approach
- Review [Contracts](contracts/quantization-interface.md) for interface specifications
