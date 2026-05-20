# Quickstart: Model Management

Get up and running with model management for your local MLX server in under 5 minutes.

## Prerequisites

- Local MLX Server repository cloned and initialized (`just init`)
- Python 3.11+ with `pyyaml` and `psutil` installed (included in project dependencies)
- At least one model profile configured in `scripts/wrapper-config/profiles.yaml`

## Step 1: List Available Model Profiles

See what models are configured and available for serving:

```bash
just models-list
```

**Expected Output**:
```
Available Model Profiles:
─────────────────────────────────────────────
Name: nemotron-120b
Path: ~/.cache/huggingface/hub/Nemotron-120B-48GB
Memory: 48.0 GB
Description: Nemotron 120B optimized for 48GB Apple Silicon
Status: Inactive

Name: gpt-oss-120b
Path: ~/.cache/huggingface/hub/GPT-OSS-120B
Memory: 48.0 GB
Description: GPT-OSS 120B with hybrid quantization
Status: Inactive
─────────────────────────────────────────────
Total: 2 profiles
Active: None
```

**JSON Output** (for scripting):
```bash
just models-list --json
```

## Step 2: Check Current Active Model

See if a model is currently selected:

```bash
just model-status
```

If no model is active, you'll see:
```
No model profile currently active.

Use 'just models-list' to see available profiles.
Use 'just model-use <profile>' to activate a profile.
```

## Step 3: Activate a Model Profile

Select a model profile for serving:

```bash
just model-use nemotron-120b
```

This will:
1. ✅ Verify the profile exists
2. ✅ Validate the model path exists
3. ✅ Check for key model files (config.json, weights)
4. ✅ Verify sufficient disk space
5. ✅ Write the active profile to `.active-model` state file

**Success Output**:
```
Activating model profile: nemotron-120b
✓ Profile found: nemotron-120b
✓ Model path exists: ~/.cache/huggingface/hub/Nemotron-120B-48GB
✓ Key files present: config.json, model weights
✓ Disk space sufficient: 120.5 GB available, 48.0 GB required
✓ Profile activated successfully

Active model: nemotron-120b
```

## Step 4: Start Server with Active Model

Once a model profile is active, start the server:

```bash
just mlx-start
```

The server will use the active model profile from `.active-model`.

## Adding New Model Profiles

To add a new model profile (e.g., Qwen3.5-122B):

1. Edit `scripts/wrapper-config/profiles.yaml`:
```yaml
profiles:
  - name: "qwen3.5-122b"
    model_path: "~/.cache/huggingface/hub/Qwen3.5-122B"
    description: "Qwen3.5 122B with 4-bit quantization"
    memory_estimate_gb: 48.0
    quantization:
      type: "uniform"
      bits: 4
      group_size: 128
    kv_cache:
      quantized: true
      bits: 4
    inference_args:
      max_context_length: 2048
      temperature: 0.7
```

2. Verify the profile is listed:
```bash
just models-list
```

3. Activate the new profile:
```bash
just model-use qwen3.5-122b
```

## Common Operations

### Check Validation Without Activating
```bash
just model-use nemotron-120b --validate
```

### Force Activation (Skip Validation)
```bash
just model-use nemotron-120b --force
```

### See Active Model Programmatically
```bash
cat .active-model
```

### Clear Active Model
```bash
rm .active-model
```

## Troubleshooting

### "Profile not found" Error
```bash
just model-use invalid-profile
# ✗ Profile not found: invalid-profile
```
**Fix**: Check available profiles with `just models-list` and use the correct name.

### "Model path does not exist" Error
```bash
just model-use nemotron-120b
# ✗ Model path does not exist: ~/.cache/huggingface/hub/Nemotron-120B-48GB
```
**Fix**: 
1. Verify the model files are downloaded
2. Update the `model_path` in `scripts/wrapper-config/profiles.yaml`
3. Use absolute paths or ensure `~` expands correctly

### "Insufficient disk space" Warning
```bash
just model-use nemotron-120b
# ⚠ Low disk space warning: 15.0 GB available, 48.0 GB required
```
**Options**:
1. Free up disk space
2. Use a more memory-efficient profile (e.g., `120b-extreme`)
3. Force activation with `--force` flag (not recommended)

### Concurrent Model Changes
If you see locking errors:
```
Error: Could not acquire lock on .active-model
```
**Fix**: Wait a few seconds and retry. Another process may be switching models.

## Next Steps

- Read the [full specification](spec.md) for detailed requirements
- Review the [data model](data-model.md) for entity definitions
- Check the [interface contract](contracts/model-management-interface.md) for command details
- See [research.md](research.md) for design decisions and alternatives considered
