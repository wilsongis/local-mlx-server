# Quickstart: MLX Server Wrapper

**Date**: 2026-05-11  
**Feature**: 004-mlx-server-wrapper  
**Status**: Complete

## Prerequisites

- Python 3.11+ with `uv` package manager
- MLX and mlx-lm installed (`uv pip install mlx-lm`)
- PyYAML, Click, and psutil (`uv pip install pyyaml click psutil`)
- Apple Silicon Mac with 48GB+ memory (for 120B+ models)
- Existing `just` command runner

---

## Installation

1. **Clone and setup** (if not already done):
   ```bash
   cd /path/to/local-mlx-server
   uv sync
   ```

2. **Verify dependencies**:
   ```bash
   just check-deps  # or manually: python -c "import mlx_lm, yaml, click, psutil"
   ```

3. **Create wrapper configuration directory**:
   ```bash
   mkdir -p scripts/wrapper-config
   ```

---

## Configuration

### 1. Create Model Profiles

Create `scripts/wrapper-config/profiles.yaml`:

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

  - name: "120b-extreme"
    model_path: "~/.cache/huggingface/hub/Nemotron-120B"
    quantization:
      type: "hybrid"
      paths:
        - pattern: ".*"
          bits: 4
          group_size: 128
    kv_cache:
      quantized: true
      bits: 4
    inference_args:
      max_context_length: 1024
      temperature: 0.7
      batch_size: 1
    description: "Minimum viable config for 120B on 48GB"
```

### 2. Create Presets (Optional)

Create `scripts/wrapper-config/presets.yaml`:

```yaml
presets:
  - name: "120b-extreme"
    target_memory_gb: 45
    model_size_class: "120B+"
    quantization_profile: "120b-extreme"
    kv_cache_bits: 4
    max_context_length: 1024
    batch_size: 1
    description: "Minimum viable config for 120B on 48GB"

  - name: "120b-balanced"
    target_memory_gb: 48
    model_size_class: "120B+"
    quantization_profile: "120b-balanced"
    kv_cache_bits: 4
    max_context_length: 2048
    batch_size: 1
    description: "Balanced performance/memory for 120B on 48GB"
```

---

## Usage

### Starting the Server

**Using just recipe** (recommended):
```bash
# Start with specific profile
just mlx-start 120b-balanced

# Start with profile and preset (applies memory optimizations)
just mlx-start 120b-balanced 120b-extreme

# Start with custom port
just mlx-start 120b-balanced "" --port 8080
```

**Using wrapper directly**:
```bash
# Start with profile
python scripts/mlx-wrapper.py start --profile 120b-balanced

# Start on custom port
python scripts/mlx-wrapper.py start --profile 120b-balanced --port 8080

# Start with preset
python scripts/mlx-wrapper.py start --profile 120b-balanced --preset 120b-extreme
```

**Expected output**:
```
[INFO] Loading profile: 120b-balanced
[INFO] Model: Nemotron-120B
[INFO] Checking memory... 48.2GB available, 45GB required ✓
[INFO] Starting server on http://127.0.0.1:8080
[INFO] Waiting for model load... (this may take 3-5 minutes)
[PROGRESS] Loading model... 45%
[PROGRESS] Loading model... 87%
[SUCCESS] Server ready at http://127.0.0.1:8080
[INFO] Health endpoint: http://127.0.0.1:8081/health
```

---

### Checking Status

```bash
# Using just
just mlx-status

# Using wrapper
python scripts/mlx-wrapper.py status

# JSON output (for scripting)
python scripts/mlx-wrapper.py status --json
```

**Expected output**:
```
Server Status: running
Model: Nemotron-120B
Profile: 120b-balanced
Uptime: 2h 34m
Memory: 45.2GB / 48GB
Active Requests: 0
```

---

### Health Checks

```bash
# Using just
just mlx-health

# Using wrapper
python scripts/mlx-wrapper.py health

# JSON output (for scripting)
python scripts/mlx-wrapper.py health --json
```

**Expected output** (JSON):
```json
{
  "status": "ready",
  "model": "Nemotron-120B",
  "model_loaded": true,
  "load_progress_pct": 100,
  "memory_usage_gb": 45.2,
  "memory_limit_gb": 48,
  "uptime_seconds": 9240,
  "active_requests": 0,
  "last_check_timestamp": "2026-05-19T21:00:00Z",
  "system": {
    "cpu_percent": 12.5,
    "memory_available_gb": 15.8,
    "disk_free_gb": 120.3
  }
}
```

---

### Stopping the Server

```bash
# Using just
just mlx-stop

# Using wrapper
python scripts/mlx-wrapper.py stop

# Force kill if graceful shutdown fails
python scripts/mlx-wrapper.py stop --force
```

---

## Testing the Server

Once the server is running and healthy, test with OpenAI-compatible API:

```bash
# Chat completion
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Nemotron-120B",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'

# List models
curl http://localhost:8080/v1/models
```

---

## Listing Profiles and Presets

```bash
# List available profiles
python scripts/mlx-wrapper.py list-profiles

# List available presets
python scripts/mlx-wrapper.py list-presets
```

---

## Troubleshooting

### Server fails to start - "Insufficient memory"
```bash
[ERROR] Only 32.5GB available, 45GB required
```
**Solution**: Close other applications, use a more aggressive preset (e.g., `120b-extreme`), or reduce `max_context_length` in profile.

### Server starts but health check fails
```bash
[ERROR] Health check timeout after 300s
```
**Solution**: 120B+ models can take 5+ minutes to load. Use `--wait` with longer timeout, or check model path in profile is correct.

### Port already in use
```bash
[ERROR] Port 8080 already in use
```
**Solution**: Use `--port 8081` (or other port), or stop existing server with `just mlx-stop`.

### Profile not found
```bash
[ERROR] Profile 'invalid-name' not found
Available profiles: 120b-balanced, 120b-extreme
```
**Solution**: Check profile name in `scripts/wrapper-config/profiles.yaml`, or use `list-profiles` to see available options.

---

## Next Steps

- Review [`plan.md`](plan.md) for implementation details
- Review [`data-model.md`](data-model.md) for configuration structure
- Review [`contracts/cli-interface.md`](contracts/cli-interface.md) for full CLI reference
- Review [`contracts/health-endpoint.md`](contracts/health-endpoint.md) for health endpoint API
