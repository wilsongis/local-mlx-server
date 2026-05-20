# Interface Contract: Model Management Commands

## Overview
This contract defines the interface for model management `just` recipes that provide model profile listing and selection capabilities for the local MLX server.

## Commands

### `just models-list`

List all available model profiles with their metadata.

**Interface**:
```bash
just models-list [--json]
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--json` | flag | No | Output in JSON format for programmatic consumption |

**Output (Human-readable)**:
```
Available Model Profiles:
─────────────────────────────────────────────
Name: nemotron-120b
Path: ~/.cache/huggingface/hub/Nemotron-120B-48GB
Memory: 48.0 GB
Description: Nemotron 120B optimized for 48GB Apple Silicon
Status: Active

Name: gpt-oss-120b
Path: ~/.cache/huggingface/hub/GPT-OSS-120B
Memory: 48.0 GB
Description: GPT-OSS 120B with hybrid quantization
Status: Inactive
─────────────────────────────────────────────
Total: 3 profiles
Active: nemotron-120b
```

**Output (JSON)**:
```json
{
  "profiles": [
    {
      "name": "nemotron-120b",
      "model_path": "~/.cache/huggingface/hub/Nemotron-120B-48GB",
      "memory_estimate_gb": 48.0,
      "description": "Nemotron 120B optimized for 48GB Apple Silicon",
      "is_active": true
    }
  ],
  "active_profile": "nemotron-120b",
  "total_count": 3
}
```

**Exit Codes**:
- `0`: Successfully listed profiles
- `1`: Error reading profiles configuration

---

### `just model-use <profile>`

Select and activate a model profile for serving.

**Interface**:
```bash
just model-use <profile> [--validate] [--force]
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `profile` | string | Yes | Name of the model profile to activate |
| `--validate` | flag | No | Run validation checks before activation (default: true) |
| `--force` | flag | No | Skip validation and force activation |

**Output (Success)**:
```
Activating model profile: nemotron-120b
✓ Profile found: nemotron-120b
✓ Model path exists: ~/.cache/huggingface/hub/Nemotron-120B-48GB
✓ Key files present: config.json, model weights
✓ Disk space sufficient: 120.5 GB available, 48.0 GB required
✓ Profile activated successfully

Active model: nemotron-120b
```

**Output (Validation Failure)**:
```
Activating model profile: invalid-profile
✗ Profile not found: invalid-profile

Available profiles:
  - nemotron-120b
  - gpt-oss-120b
  - qwen3.5-122b

Use 'just models-list' to see all available profiles.
```

**Output (With Warnings)**:
```
Activating model profile: nemotron-120b
✓ Profile found: nemotron-120b
✓ Model path exists: ~/.cache/huggingface/hub/Nemotron-120B-48GB
⚠ Low disk space warning: 15.0 GB available, 48.0 GB required
  Model may run but system will be memory-constrained.
✓ Profile activated successfully (with warnings)

Active model: nemotron-120b
```

**Exit Codes**:
- `0`: Profile activated successfully
- `1`: Profile not found or critical validation failure
- `2`: Profile activated with warnings

---

### `just model-status`

Display the currently active model profile.

**Interface**:
```bash
just model-status
```

**Output (Active Model)**:
```
Current Model Profile: nemotron-120b
Path: ~/.cache/huggingface/hub/Nemotron-120B-48GB
Memory: 48.0 GB
Description: Nemotron 120B optimized for 48GB Apple Silicon
```

**Output (No Active Model)**:
```
No model profile currently active.

Use 'just models-list' to see available profiles.
Use 'just model-use <profile>' to activate a profile.
```

**Exit Codes**:
- `0`: Successfully displayed status (or no active model)
- `1`: Error reading state file

## Validation Contract

### ValidationResult Schema

Used internally by `model-use` and available for programmatic access.

```json
{
  "profile_name": "nemotron-120b",
  "is_valid": true,
  "errors": [],
  "warnings": [
    "Low disk space: 15.0 GB available, 48.0 GB required"
  ],
  "path_exists": true,
  "key_files_present": ["config.json", "model.safetensors"],
  "missing_files": [],
  "disk_space_gb_available": 15.0,
  "disk_space_gb_required": 48.0,
  "validation_timestamp": "2026-05-20T18:54:00Z"
}
```

## Error Handling

All commands must:
1. Provide clear, actionable error messages
2. Suggest next steps or available alternatives
3. Use consistent exit codes
4. Log errors to stderr, output to stdout (for piping)
