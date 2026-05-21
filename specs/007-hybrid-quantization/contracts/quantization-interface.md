# Contract: Quantization Interface for Local MLX Server

## Overview
This contract defines the interface for per-path hybrid quantization configuration in the local MLX server infrastructure. It covers CLI arguments, just recipes, health endpoint extensions, and profile schema.

## 1. Quantization Profile Schema (YAML)

**Location**: `scripts/wrapper-config/profiles.yaml`

```yaml
quantization_profiles:
  <preset_name>:
    version: string              # Semver (e.g., "1.0.0")
    preset_name: string           # Optional human-readable name (e.g., "tq3a-tq2e-g32")
    attention_bits: integer       # 2-8, bits for attention layers
    expert_bits: integer          # 2-8, bits for expert layers (MoE models)
    group_size: integer           # 16, 32, 64, or 128
    calibration_method: string    # "none" or "lloyd-max"
    model_patterns: array[string] # Regex patterns for auto-matching models
    calibration_data_path: string # Optional path to calibration dataset
```

**Validation Rules**:
- `attention_bits` and `expert_bits`: Integer between 2 and 8 (ERR-001)
- `group_size`: Must be one of [16, 32, 64, 128] (ERR-006)
- `calibration_method`: Must be "none" or "lloyd-max"
- `model_patterns`: Array of valid regex strings

## 2. mlx_lm.server CLI Integration

### CLI Arguments

| Argument | Type | Required | Description |
|-----------|------|----------|-------------|
| `--quant-config <path>` | string | No | Path to QuantizationProfile YAML file |
| `--calibration-data <path>` | string | No | Path to CalibrationDataset for Lloyd-Max |

### Environment Variable Alternative

| Variable | Type | Description |
|----------|------|-------------|
| `MLX_QUANT_PROFILE` | string | Path to quantization profile (alternative to `--quant-config`) |

**Precedence**: CLI argument > Environment variable > Default (no quantization)

## 3. Just Recipes

### `just quant-list`
List all available quantization profiles in `scripts/wrapper-config/profiles.yaml`.

**Output Format**:
```
Available Quantization Profiles:
  - tq3a-tq2e-g32 (attention: 3-bit, expert: 2-bit, group: 32)
  - tq4a-tq4e-g32 (attention: 4-bit, expert: 4-bit, group: 32)
```

### `just quant-validate <profile>`
Validate a quantization profile YAML file for syntax and compatibility.

**Arguments**:
- `<profile>`: Path to YAML profile file or preset name

**Exit Codes**:
- 0: Validation passed
- 1: Validation failed (syntax error, invalid values)

**Output**: Validation errors with line numbers if applicable (ERR-001, ERR-006)

### `just quant-apply <model> <profile>`
Apply quantization profile to specified model.

**Arguments**:
- `<model>`: Model name or path
- `<profile>`: Quantization profile preset name or path to YAML

**Behavior**:
1. Validate profile
2. Detect model architecture (MoE vs standard)
3. Apply per-path quantization during model load
4. Update `.active-model` with quantized model reference

**Errors**: ERR-002 (unsupported architecture), ERR-004 (checksum mismatch)

### `just quant-calibrate <dataset> <output>`
Run Lloyd-Max calibration with provided dataset.

**Arguments**:
- `<dataset>`: Path to calibration data (JSON, numpy, or text)
- `<output>`: Output path for generated codebooks

**Output**: Generated `.mlx` codebook files in `scripts/wrapper-config/codebooks/`

**Errors**: ERR-003 (invalid format)

### `just quant-status`
Show current quantization status for active model.

**Output Format**:
```
Active Model: Nemotron-3-Super-120B-A12B
Quantization Profile: tq3a-tq2e-g32
  - Attention layers: 3-bit, group 32
  - Expert layers: 2-bit, group 32
  - Calibration: none
Memory Estimate: 48.0 GB
```

## 4. Health Endpoint Extension

### GET /health (Extended)

**Response JSON Schema Addition**:
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

**Fields**:
- `quantization.profile`: Active preset name or "custom"
- `quantization.attention_bits`: Current attention layer bit-width
- `quantization.expert_bits`: Current expert layer bit-width (0 for non-MoE)
- `quantization.group_size`: Quantization group size
- `quantization.calibration_method`: Active calibration method
- `quantization.model_architecture`: Detected architecture name
- `quantization.is_moe`: Whether model uses mixture-of-experts
- `quantization.expert_count`: Number of experts (0 if not MoE)
- `quantization.active_params`: Active parameters (for MoE sparse activation)
- `quantization.total_params`: Total model parameters

## 5. Error Response Format

All quantization errors return JSON with the following structure:

```json
{
  "error": {
    "code": "ERR-001",
    "message": "Invalid bit-width: 9. Must be between 2 and 8.",
    "details": {
      "field": "attention_bits",
      "value": 9,
      "valid_range": [2, 8]
    }
  }
}
```

**HTTP Status Codes**:
- 400: Bad Request (ERR-001, ERR-003, ERR-006)
- 422: Unprocessable Entity (ERR-002, ERR-004)
- 507: Insufficient Storage (ERR-005)

## 6. CalibrationDataset Format

### JSON Format
```json
{
  "samples": [
    [101, 202, 345, ...],
    [102, 203, 456, ...]
  ]
}
```

### Numpy Format
`.npy` file with shape `(sample_count, sequence_length)` containing token IDs.

### Text Format
Plain text file, one sample per line or continuous text (will be tokenized with model tokenizer).

## 7. Codebook Binary Format

**Location**: `scripts/wrapper-config/codebooks/{codebook_id}.mlx`

MLX serialized array containing Lloyd-Max optimized lookup table for quantization.

**Metadata** (stored in profile or separate `.json`):
```json
{
  "codebook_id": "uuid",
  "algorithm_version": "V3",
  "bits": 3,
  "group_size": 32,
  "model_layers": ["attention.q_proj", "attention.k_proj"],
  "generated_at": "2026-05-20T21:35:00Z",
  "perplexity_improvement": 12.5
}
```
