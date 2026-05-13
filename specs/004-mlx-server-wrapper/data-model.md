# Data Model: MLX Server Wrapper

**Date**: 2026-05-11  
**Feature**: 004-mlx-server-wrapper  
**Status**: Complete

## Entities

### 1. ModelProfile

Configuration entity defining model path, quantization settings, KV cache compression, and inference arguments.

**Fields**:
- `name` (string, required): Unique profile identifier (e.g., "120b-balanced")
- `model_path` (string, required): Absolute or `~`-expanded path to model directory
- `quantization` (object, required): Quantization configuration
  - `type` (string, enum: "uniform" | "hybrid", required): Quantization strategy
  - `bits` (integer, optional): Default bits for uniform quantization
  - `group_size` (integer, optional): Group size for uniform quantization
  - `paths` (array of QuantizationPath, optional): Per-path config for hybrid
- `kv_cache` (object, optional): KV cache compression settings
  - `quantized` (boolean, default: false): Enable KV cache quantization
  - `bits` (integer, default: 4): Bits for KV cache quantization
- `inference_args` (object, optional): mlx_lm.server arguments
  - `max_context_length` (integer, default: 2048)
  - `temperature` (float, default: 0.7)
  - `max_tokens` (integer, default: 4096)
  - `batch_size` (integer, default: 1)
- `description` (string, optional): Human-readable description

**Validation Rules**:
- `name` must match pattern `^[a-z0-9-]+$`
- `model_path` must exist and be a directory
- For `type: "uniform"`, `bits` must be 4, 8, or 16
- For `type: "hybrid"`, `paths` array must be non-empty
- `max_context_length` must be positive integer ≤ 8192
- `temperature` must be float between 0.0 and 2.0

**State Transitions**: N/A (configuration entity, not stateful)

---

### 2. StartupPreset

Named configuration targeting specific model size classes with memory-optimized defaults.

**Fields**:
- `name` (string, required): Unique preset identifier (e.g., "120b-extreme")
- `target_memory_gb` (float, required): Target memory consumption in GB
- `model_size_class` (string, enum: "7B", "13B", "30B", "70B", "120B+", required): Target model size
- `quantization_profile` (string, required): Reference to ModelProfile name
- `kv_cache_bits` (integer, default: 4): KV cache quantization bits
- `max_context_length` (integer, default: 1024): Context length limit
- `batch_size` (integer, default: 1): Batch size (must be 1 for 120B+)
- `description` (string, optional): Human-readable description

**Validation Rules**:
- `target_memory_gb` must be positive float ≤ 128.0
- `quantization_profile` must reference existing ModelProfile name
- For `model_size_class: "120B+"`, `batch_size` must be 1
- `max_context_length` must be ≤ 2048 for 120B+ presets

**Relationships**:
- References `ModelProfile.name` via `quantization_profile`

---

### 3. HealthStatus

Runtime entity tracking server state with model loading progress.

**Fields**:
- `status` (string, enum: "initializing" | "ready" | "degraded" | "down", required): Server state
- `model` (string, optional): Model name/identifier
- `model_loaded` (boolean, required): Whether model is fully loaded
- `load_progress_pct` (integer, min: 0, max: 100): Loading progress percentage
- `memory_usage_gb` (float, optional): Current memory consumption
- `memory_limit_gb` (float, optional): Configured memory limit
- `uptime_seconds` (integer, optional): Server uptime in seconds
- `active_requests` (integer, default: 0): Current active inference requests
- `last_check_timestamp` (ISO8601 datetime, required): Health check time

**Validation Rules**:
- `status: "ready"` requires `model_loaded: true` and `load_progress_pct: 100`
- `memory_usage_gb` must be ≤ `memory_limit_gb` when both present
- `active_requests` must be non-negative
- `load_progress_pct` must be 0-100

**State Transitions**:
```
initializing --model loaded--> ready
initializing --load failed--> down
ready --high memory/errors--> degraded
degraded --recovery--> ready
degraded --persistent errors--> down
ready --shutdown--> down
```

---

### 4. QuantizationPath

Per-path quantization configuration for hybrid quantization.

**Fields**:
- `pattern` (string, required): Regex or glob pattern matching layer/path names
- `bits` (integer, required): Quantization bits (4, 8, or 16)
- `group_size` (integer, default: 64): Group size for quantization
- `description` (string, optional): Human-readable description of matched layers

**Validation Rules**:
- `pattern` must be valid regex or glob pattern
- `bits` must be 4, 8, or 16
- `group_size` must be positive power of 2 (64, 128, 256)

**Relationships**:
- Contained within `ModelProfile.quantization.paths`

---

## Relationships Diagram

```
StartupPreset
  │
  │ references (quantization_profile)
  ▼
ModelProfile
  │
  │ contains (quantization.paths)
  ▼
QuantizationPath

HealthStatus (runtime, no persistent relationships)
```

## Configuration File Formats

### profiles.yaml

```yaml
profiles:
  - name: "120b-balanced"
    model_path: "~/.cache/huggingface/hub/Nemotron-120B"
    quantization:
      type: "hybrid"
      paths:
        - pattern: "attention.*"
          bits: 8
          group_size: 64
        - pattern: "ffn.*"
          bits: 4
          group_size: 128
    kv_cache:
      quantized: true
      bits: 4
    inference_args:
      max_context_length: 2048
      temperature: 0.7
      batch_size: 1
    description: "Balanced performance/memory for 120B on 48GB"
```

### presets.yaml

```yaml
presets:
  - name: "120b-extreme"
    target_memory_gb: 45
    model_size_class: "120B+"
    quantization_profile: "120b-balanced"
    kv_cache_bits: 4
    max_context_length: 1024
    batch_size: 1
    description: "Minimum viable config for 120B on 48GB"
```

## Validation Rules Summary

| Entity | Field | Rule |
|--------|-------|------|
| ModelProfile | name | `^[a-z0-9-]+$` |
| ModelProfile | quantization.type | "uniform" or "hybrid" |
| ModelProfile | quantization.paths | Required if type="hybrid" |
| StartupPreset | target_memory_gb | 0 < value ≤ 128 |
| StartupPreset | batch_size | Must be 1 if model_size_class="120B+" |
| HealthStatus | status | Valid enum value |
| HealthStatus | load_progress_pct | 0 ≤ value ≤ 100 |
| QuantizationPath | bits | 4, 8, or 16 |
| QuantizationPath | group_size | Power of 2 (64, 128, 256) |
