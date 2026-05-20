# Data Model: Model Management

## Entities

### ModelProfile
Represents a configured large language model with its quantization and inference settings.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Unique identifier for the profile (e.g., "nemotron-120b") |
| model_path | string | Yes | Filesystem path to model files (supports ~ expansion) |
| description | string | No | Human-readable description of the profile |
| memory_estimate_gb | float | No | Estimated memory requirement in GB (from profiles.yaml or computed) |
| quantization | object | No | Quantization configuration (type, paths, bits, group_size) |
| kv_cache | object | No | KV cache settings (quantized, bits) |
| inference_args | object | No | Model inference parameters (max_context_length, temperature, etc.) |

**Example**:
```yaml
- name: "nemotron-120b"
  model_path: "~/.cache/huggingface/hub/Nemotron-120B-48GB"
  description: "Nemotron 120B optimized for 48GB Apple Silicon"
  memory_estimate_gb: 48.0
  quantization:
    type: "hybrid"
    paths:
      - pattern: "attention.*"
        bits: 8
        group_size: 64
  kv_cache:
    quantized: true
    bits: 4
  inference_args:
    max_context_length: 2048
    temperature: 0.7
```

### ModelRegistry
Collection of all configured model profiles with lookup and enumeration capabilities.

| Field | Type | Description |
|-------|------|-------------|
| profiles | list[ModelProfile] | All configured model profiles |
| active_profile_name | string or None | Name of currently active profile (from .active-model) |

**Methods**:
- `list_profiles() -> list[ModelProfile]`: Return all profiles
- `get_profile(name: str) -> ModelProfile or None`: Lookup by name
- `validate_profile(name: str) -> ValidationResult`: Run all validations
- `set_active_profile(name: str) -> bool`: Set active profile with locking
- `get_active_profile() -> str or None`: Read current active profile

### ValidationResult
Outcome of validating a model profile against filesystem and system constraints.

| Field | Type | Description |
|-------|------|-------------|
| profile_name | string | Name of the validated profile |
| is_valid | boolean | Whether all critical checks passed |
| errors | list[string] | Critical failures that prevent model use |
| warnings | list[string] | Non-critical issues (e.g., low disk space) |
| path_exists | boolean | Whether model path exists |
| key_files_present | list[string] | List of found key model files |
| missing_files | list[string] | List of missing key model files |
| disk_space_gb_available | float | Available space in GB at model path |
| disk_space_gb_required | float | Estimated requirement from profile |
| validation_timestamp | string | ISO 8601 timestamp of validation |

**Validation Rules**:
1. **Path Existence** (Critical): `model_path` must exist on filesystem
2. **Key Files** (Warning): Check for `config.json`, model weight files (*.safetensors, *.npz)
3. **Disk Space** (Warning/Critical): Available space > required (critical if < 1GB buffer)
4. **Profile Exists** (Critical): Profile name must exist in registry

### StateFile (.active-model)
Simple text file storing the currently active model profile name.

**Format**: Plain text, single line with profile name
**Example**:
```
nemotron-120b
```

**Concurrency**: Protected by `flock()` on the state file. Exclusive lock during writes.

## Relationships

```
ModelRegistry (1) ────> (0..n) ModelProfile
ModelProfile (1) ────> (1) ValidationResult
ModelRegistry (1) ────> (0..1) StateFile [.active-model]
```

## State Transitions

### Model Profile Activation
```
[No Active Model] ──> [Lock State File] ──> [Write Profile Name] ──> [Release Lock] ──> [Active: profile X]
[Active: profile X] ──> [Lock State File] ──> [Write Profile Name] ──> [Release Lock] ──> [Active: profile Y]
```

### Validation Flow
```
[Profile Selected] ──> [Check Path Exists] ──> [Check Key Files] ──> [Check Disk Space] ──> [Return ValidationResult]
```

## File Locations

| Artifact | Path | Format |
|----------|------|--------|
| Profile Registry | `scripts/wrapper-config/profiles.yaml` | YAML |
| Active Model State | `.active-model` (project root) | Plain text |
| Model Management Script | `scripts/model-management.py` | Python |
| just Recipes | `justfile` | just syntax |
