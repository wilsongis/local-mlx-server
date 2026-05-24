# Operations Guide

## Overview

This guide covers all operational aspects of running the Local MLX Server, including server lifecycle management, model operations, troubleshooting procedures, and model profile selection for Apple Silicon memory-constrained systems.

The `just` command bridge is the primary control interface for all operational workflows. Using `just` recipes ensures reproducibility across machines and sessions.

---

## Just Recipe Reference

This section documents all `just` recipes with command syntax, required arguments, examples, edge cases, and developer contribution guidelines.

### Recipe Index

| Recipe | Description | Section |
|---------|-------------|---------|
| `just` / `just default` | Show available commands | [default](#default) |
| `just start` | Start server in containerized environment | [start](#start) |
| `just build` | Build/rebuild container image | [build](#build) |
| `just run` | Start server natively with mlx_lm.server | [run](#run) |
| `just status` | Check container status | [status](#status) |
| `just stop` | Stop running server container | [stop](#stop) |
| `just init` | Initialize virtual environment and install | [init](#init) |
| `just lint` | Run linting and formatting (ruff) | [lint](#lint) |
| `just test` | Run test suite (pytest) | [test](#test) |
| `just verify` | Run lint + test (full verification) | [verify](#verify) |
| `just doctor` | Run environment health checks | [doctor](#doctor) |
| `just security-check` | Validate security configuration | [security-check](#security-check) |
| `just mlx-start` | Start MLX server with wrapper (profile/preset) | [mlx-start](#mlx-start) |
| `just mlx-stop` | Stop MLX server via wrapper | [mlx-stop](#mlx-stop) |
| `just mlx-status` | Check MLX server status via wrapper | [mlx-status](#mlx-status) |
| `just mlx-health` | Check MLX server health via wrapper | [mlx-health](#mlx-health) |
| `just mlx-list-profiles` | List available model profiles | [mlx-list-profiles](#mlx-list-profiles) |
| `just mlx-list-presets` | List available startup presets | [mlx-list-presets](#mlx-list-presets) |
| `just server-start` | Start MLX server with lifecycle management (PID, port conflict) | [server-start](#server-start) |
| `just server-stop` | Stop MLX server with graceful shutdown (SIGTERM -> SIGKILL) | [server-stop](#server-stop) |
| `just server-status` | Check server status (process, health, uptime) | [server-status](#server-status) |
| `just server-config` | Display server lifecycle configuration | [server-config](#server-config)(#server-config) |
| `just kv-status` | Show KV cache compression status | [kv-status](#kv-status) |
| `just kv-enable` | Enable KV cache compression with profile | [kv-enable](#kv-enable) |
| `just kv-disable` | Disable KV cache compression | [kv-disable](#kv-disable) |
| `just kv-list-profiles` | List available KV cache profiles | [kv-list-profiles](#kv-list-profiles) |
| `just kv-validate` | Validate KV cache profile configuration | [kv-validate](#kv-validate) |

---

### default

**Description**: Show all available `just` recipes.

**Syntax**:
```bash
just
# or explicitly
just default
```

**Examples**:
```bash
$ just
Available recipes:
    build                   # Build/Rebuild the container image
    default                 # Default: Show available commands
    doctor                  # Health check for local MLX server environment
    init                    # Initialize local virtual environment and editable install
    lint                    # Run linting and formatting
    run                     # Start server natively with mlx_lm.server
    security-check          # Validate security configuration
    start                   # Build container if needed and start the server (containerized)
    status                  # Container status helper
    stop                    # Stop local server container
    test                    # Run the test suite
    verify                  # Verify standard: run linters, formatters, and tests
```

**Edge Cases**:
- No edge cases (built-in `just` functionality)

---

### start

**Description**: Build container if needed and start the server in a containerized environment.

**Syntax**:
```bash
just start
```

**Environment Variables**:
| Variable | Default | Description |
|----------|---------|-------------|
| `IMAGE_NAME` | `local-mlx-server` | Container image name |
| `CONTAINER_NAME` | `local-mlx-server` | Container instance name |
| `PORT` | `8000` | Port to expose |
| `HOST` | `127.0.0.1` | Host to bind to |

**Examples**:
```bash
# Start with defaults
$ just start
Starting local MLX server container...
Container not found, building image...
Building Podman image...
[... build output ...]
Server is live at http://127.0.0.1:8000

# Start with custom port
$ PORT=8080 just start
```

**Edge Cases**:
- **Container already exists but is stopped**: `just start` will start the existing container.
- **Port already in use**: Podman will fail with port conflict error. See [Port Conflicts](#port-conflicts).
- **Image not found**: `just start` automatically runs `just build` to create the image.
- **Build fails**: Container will not start. Check build logs and fix issues before retrying.

---

### build

**Description**: Build or rebuild the container image from the Containerfile.

**Syntax**:
```bash
just build
```

**Environment Variables**:
| Variable | Default | Description |
|----------|---------|-------------|
| `IMAGE_NAME` | `local-mlx-server` | Container image name |

**Examples**:
```bash
# Build with default settings
$ just build
Building Podman image...
[... build output ...]
```

**Edge Cases**:
- **Containerfile not found**: Podman will fail with "error reading Containerfile".
- **Build cache issues**: Use `podman build --no-cache -t local-mlx-server .` manually if needed.
- **Out of disk space**: Podman will fail. Clean up with `podman system prune`.

---

### run

**Description**: Start the server natively using `mlx_lm.server` via `uv`.

**Syntax**:
```bash
just run
```

**Environment Variables**:
| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_PATH` | `./models` | Path to model directory |
| `HOST` | `127.0.0.1` | Host to bind to |
| `PORT` | `8000` | Port to listen on |
| `MAX_TOKENS` | `4096` | Maximum KV cache size |

**Examples**:
```bash
# Run with defaults
$ just run
Starting mlx_lm.server via uv...
[... server startup output ...]

# Run with custom model path
$ MODEL_PATH=./models/nemotron-120b-q2 just run

# Run with custom port and host
$ HOST=0.0.0.0 PORT=8080 just run
```

**Edge Cases**:
- **MODEL_PATH not found**: Server will fail to start. Verify path exists and is accessible.
- **Port already in use**: Server will fail with "Address already in use". See [Port Conflicts](#port-conflicts).
- **Out of memory**: Server may crash during model load. See [Memory Issues](#memory-issues).
- **mlx_lm not installed**: Run `just init` to set up the environment first.

---

### status

**Description**: Check the status of the containerized server.

**Syntax**:
```bash
just status
```

**Environment Variables**:
| Variable | Default | Description |
|----------|---------|-------------|
| `CONTAINER_NAME` | `local-mlx-server` | Container instance name |

**Examples**:
```bash
# Check status
$ just status
CONTAINER ID   IMAGE                  COMMAND                  CREATED         STATUS         PORTS                    NAMES
abc123def456   local-mlx-server       python -m mlx_lm.s...   2 minutes ago   Up 2 minutes   0.0.0.0:8000->8000/tcp   local-mlx-server

# If container is not running
$ just status
CONTAINER ID   IMAGE   COMMAND   CREATED   STATUS   PORTS   NAMES
# (empty output)
```

**Edge Cases**:
- **Container not found**: Returns empty output (no error).
- **Podman not running**: Command will fail with Podman daemon error.

---

### stop

**Description**: Stop the running server container.

**Syntax**:
```bash
just stop
```

**Environment Variables**:
| Variable | Default | Description |
|----------|---------|-------------|
| `CONTAINER_NAME` | `local-mlx-server` | Container instance name |

**Examples**:
```bash
# Stop the server
$ just stop
local-mlx-server
```

**Edge Cases**:
- **Container already stopped**: Command succeeds silently (uses `-` prefix for error suppression).
- **Container not found**: Command succeeds silently.
- **Podman not running**: Command will fail with Podman daemon error.

---

### init

**Description**: Initialize the local virtual environment and install the project in editable mode.

**Syntax**:
```bash
just init
```

**Examples**:
```bash
# Initialize project
$ just init
Using Python 3.12.0
Creating virtual environment at .venv
uv pip install -e .
[... installation output ...]
Project initialized.
```

**Edge Cases**:
- **Already initialized**: `uv venv` will skip creation if `.venv` exists. Re-run `uv pip install -e .` to update.
- **uv not installed**: Command will fail. Install uv from https://docs.astral.sh/uv/getting-started/installation/
- **Dependencies fail to install**: Check error messages and resolve system dependencies.

---

### lint

**Description**: Run linting and formatting checks using Ruff.

**Syntax**:
```bash
just lint
```

**Examples**:
```bash
# Run linter and formatter
$ just lint
Running ruff check...
All checks passed!
Running ruff format...
All formatted!
```

**Edge Cases**:
- **Linting errors found**: Ruff will attempt to fix (`--fix`) automatically. Review changes.
- **Formatting changes needed**: Ruff will reformat files automatically.
- **Configuration issues**: Ensure `pyproject.toml` has valid Ruff configuration.

---

### test

**Description**: Run the test suite using pytest.

**Syntax**:
```bash
just test
```

**Examples**:
```bash
# Run tests
$ just test
============================= test session starts ==============================
platform darwin -- Python 3.12.0, pytest-8.0.0
collected 5 items

tests/test_main.py .....                                              [100%]

============================== 5 passed in 0.50s ==============================
```

**Edge Cases**:
- **Tests fail**: Review test output and fix failing tests.
- **No tests found**: Ensure test files are in `tests/` directory with `test_*.py` naming.
- **Import errors**: Run `just init` to ensure environment is properly set up.

---

### verify

**Description**: Run full verification: linting, formatting, and tests.

**Syntax**:
```bash
just verify
```

**Examples**:
```bash
# Run full verification
$ just verify
Running ruff check...
All checks passed!
Running ruff format...
All formatted!
Running tests...
============================= test session starts ==============================
collected 5 items

tests/test_main.py .....                                              [100%]

============================== 5 passed in 0.50s ==============================
Verification complete.
```

**Edge Cases**:
- **Lint fails**: Verification stops after lint (lint runs before test).
- **Tests fail**: Verification reports failure. Fix tests and re-run.

---

### doctor

**Description**: Run environment health checks for uv, mlx_lm, model path, and port availability.

**Syntax**:
```bash
just doctor
```

**Examples**:
```bash
# Run health checks
$ just doctor
Running health checks...
Checking uv installation...
uv 0.1.0
Checking mlx_lm availability...
mlx_lm version: 0.12.0
Checking model path (./models)...
Model path ./models found.
Checking default port 8000...
Port 8000 is free.
Health check complete.
```

**Edge Cases**:
- **uv not found**: Doctor fails with installation instructions.
- **mlx_lm not found**: Doctor fails. Run `just init` to install.
- **Model path not found**: Doctor fails. Set `MODEL_PATH` or create the directory.
- **Port in use**: Doctor warns but continues (non-fatal).

---

### security-check

**Description**: Validate security configuration by running the security-check script.

**Syntax**:
```bash
just security-check
```

**Examples**:
```bash
# Run security check
$ just security-check
Running security configuration check...
Checking .env.example...
  ALLOW_NETWORK_BINDING=false ✓
  MLX_SERVER_HOST="127.0.0.1" ✓
  REDACT_SENSITIVE_VARS=true ✓
  AUTHORIZED_MODEL_DIRS configured ✓
Security check passed.
```

**Edge Cases**:
- **Script not found**: Command fails. Verify `scripts/security-check.sh` exists.
- **Security violations**: Script exits with error. Review output and fix `.env.example`.
- **.env file permissions**: Script warns if `.env` is not 600.

---

### mlx-start

**Description**: Start MLX server with wrapper using a model profile and optional preset.

**Syntax**:
```bash
just mlx-start --profile PROFILE_NAME [--preset PRESET_NAME] [--port PORT] [--host HOST]
```

**Arguments**:
- `--profile TEXT` (required): Model profile name as defined in `scripts/wrapper-config/profiles.yaml`
- `--preset TEXT` (optional): Startup preset name from `scripts/wrapper-config/presets.yaml`
- `--port INTEGER` (default: 8080): Server port
- `--host TEXT` (default: "127.0.0.1"): Server host

**Environment Variables**:
| Variable | Default | Description |
|----------|---------|-------------|
| `MLX_WRAPPER_CONFIG` | `scripts/wrapper-config/profiles.yaml` | Path to profiles config |
| `MLX_WRAPPER_PRESETS` | `scripts/wrapper-config/presets.yaml` | Path to presets config |

**Examples**:
```bash
# Start with a profile
just mlx-start --profile 120b-balanced

# Start with profile and preset
just mlx-start --profile 120b-extreme --preset 120b-extreme

# Start with custom port
just mlx-start --profile 120b-balanced --port 8080
```

**Edge Cases**:
- **Profile not found**: Wrapper exits with error listing available profiles.
- **Port already in use**: Wrapper fails to start, check with `lsof -i :8080`.
- **Insufficient memory**: Wrapper warns and suggests alternative presets.
- **Model path not found**: Wrapper exits with error indicating invalid model path.

---

### mlx-stop

**Description**: Stop running MLX server via the wrapper.

**Syntax**:
```bash
just mlx-stop [--force] [--timeout SECONDS]
```

**Arguments**:
- `--force`: Force kill if graceful shutdown fails
- `--timeout INTEGER` (default: 30): Seconds to wait for graceful shutdown

**Examples**:
```bash
# Graceful stop
just mlx-stop

# Force stop
just mlx-stop --force
```

**Edge Cases**:
- **No server running**: Command succeeds silently.
- **Server unresponsive**: Use `--force` to send SIGKILL after timeout.

---

### mlx-status

**Description**: Check MLX server status via the wrapper.

**Syntax**:
```bash
just mlx-status [--json]
```

**Arguments**:
- `--json`: Output status in JSON format

**Examples**:
```bash
# Human-readable status
just mlx-status

# JSON output
just mlx-status --json
```

**Edge Cases**:
- **No server running**: Reports server as down.
- **Server starting up**: Reports status as "initializing".

---

### mlx-health

**Description**: Check MLX server health endpoint via the wrapper.

**Syntax**:
```bash
just mlx-health
```

**Examples**:
```bash
# Check health
just mlx-health
```

**Edge Cases**:
- **Server not running**: Reports health as "down".
- **Server still loading**: Reports status as "initializing" with progress.

---

### mlx-list-profiles

**Description**: List available model profiles from configuration.

**Syntax**:
```bash
just mlx-list-profiles [--json]
```

**Arguments**:
- `--json`: Output in JSON format

**Examples**:
```bash
# List profiles
just mlx-list-profiles

# JSON output
just mlx-list-profiles --json
```

**Edge Cases**:
- **Config file not found**: Exits with error indicating missing config.
- **Invalid YAML**: Exits with error showing parse details.

---

### mlx-list-presets

**Description**: List available startup presets for different memory tiers.

**Syntax**:
```bash
just mlx-list-presets [--json]
```

**Arguments**:
- `--json`: Output in JSON format

**Examples**:
```bash
# List presets
just mlx-list-presets

# JSON output
just mlx-list-presets --json
```

**Edge Cases**:
- **Config file not found**: Exits with error indicating missing config.
- **Invalid YAML**: Exits with error showing parse details.

---

### server-start

**Description**: Start MLX server with lifecycle management (PID file, port conflict detection, graceful startup).

**Syntax**:
```bash
just server-start [MODEL_PATH]
```

**Environment Variables**:
| Variable | Default | Description |
|----------|---------|-------------|
| `SERVER_PID_FILE` | `/tmp/mlx-server.pid` | Path to PID file |
| `SERVER_GRACEFUL_TIMEOUT` | `30` | Graceful shutdown timeout (seconds) |
| `SERVER_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `MODEL_PATH` | `./models` | Path to model directory |
| `HOST` | `127.0.0.1` | Host to bind to |
| `PORT` | `8000` | Port to listen on |

**Examples**:
```bash
# Start with default settings
just server-start

# Start with custom model path
MODEL_PATH=/path/to/model just server-start

# Start with custom port
PORT=8080 just server-start
```

**Edge Cases**:
- **Server already running**: Fails with "Server already running" message.
- **Port already in use**: Detects conflict and reports conflicting PID.
- **Stale PID file**: Automatically detects and removes stale PID files.
- **Model path not found**: Server fails to start. Verify path exists.

---

### server-stop

**Description**: Stop MLX server with graceful shutdown (SIGTERM -> wait -> SIGKILL).

**Syntax**:
```bash
just server-stop
```

**Environment Variables**:
| Variable | Default | Description |
|----------|---------|-------------|
| `SERVER_PID_FILE` | `/tmp/mlx-server.pid` | Path to PID file |
| `SERVER_GRACEFUL_TIMEOUT` | `30` | Graceful shutdown timeout (seconds) |

**Examples**:
```bash
# Graceful stop
just server-stop

# Stop with custom timeout
SERVER_GRACEFUL_TIMEOUT=60 just server-stop
```

**Edge Cases**:
- **No server running**: Succeeds silently (no-op).
- **Server unresponsive**: After timeout, sends SIGKILL to force termination.
- **PID file missing**: Succeeds silently (assumes server not running).

---

### server-status

**Description**: Check MLX server status (process, health endpoint, uptime).

**Syntax**:
```bash
just server-status
```

**Environment Variables**:
| Variable | Default | Description |
|----------|---------|-------------|
| `SERVER_PID_FILE` | `/tmp/mlx-server.pid` | Path to PID file |
| `HOST` | `127.0.0.1` | Host to check |
| `PORT` | `8000` | Port to check |

**Examples**:
```bash
# Check status
just server-status

# Human-readable output
$ just server-status
Server Status: HEALTHY
  PID: 12345
  Uptime: 5 minutes
  Port: 8080
  Health: healthy
```

**Edge Cases**:
- **Server not running**: Reports status as "stopped" or "stale_pid".
- **Server starting up**: May report as "degraded" if health check not ready.
- **Health endpoint down**: Reports status as "degraded".

---

### server-config

**Description**: Display current server lifecycle configuration.

**Syntax**:
```bash
just server-config
```

**Examples**:
```bash
# Display configuration
$ just server-config
Server Lifecycle Configuration:
  PID File: /tmp/mlx-server.pid
  Graceful Timeout: 30s
  Log Level: INFO
  Model Path: ./models
  Host: 127.0.0.1
  Port: 8000

To change defaults, edit these variables at the top of the justfile:
  SERVER_PID_FILE, SERVER_GRACEFUL_TIMEOUT, SERVER_LOG_LEVEL, MODEL_PATH, HOST, PORT
```

**Edge Cases**:
- **Configuration not set**: Shows default values from justfile.

---
---

### kv-status

**Description**: Show current KV cache compression status.

**Syntax**:
```bash
just kv-status
```

**Examples**:
```bash
# Check compression status
$ just kv-status
KV Cache Compression Status:
{
  "enabled": true,
  "available": true,
  "active": true,
  "profile": "auto",
  "profile_path": "v2",
  "bits": 3,
  "model_size_class": "100B+",
  "weight_bits": 3,
  "fallback_on_error": true
}
```

**Edge Cases**:
- **Compression not available**: Shows `"available": false` if `turboquant-mlx` not installed.
- **Compression disabled**: Shows `"enabled": false`.
- **No model loaded**: Shows `"model_size_class": null`.

---

### kv-enable

**Description**: Enable KV cache compression with specified profile.

**Syntax**:
```bash
just kv-enable PROFILE="auto" BITS=3 GROUP_SIZE=64
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `PROFILE` | string | No | Compression profile: "auto", "v2-speed", "v3-quality" (default: "auto") |
| `BITS` | int | No | Bit-width for compression: 2, 3, or 4 (default: 3) |
| `GROUP_SIZE` | int | No | Elements per normalization group, must be power of 2 (default: 64) |

**Environment Variables**:
| Variable | Default | Description |
|----------|---------|-------------|
| `KV_CACHE_PROFILE` | `auto` | Compression profile to use |
| `KV_CACHE_BITS` | `3` | Bit-width for KV cache quantization |
| `KV_CACHE_GROUP_SIZE` | `64` | Group size for RMS normalization |

**Examples**:
```bash
# Enable with auto profile (recommended)
$ just kv-enable auto 3
Enabling KV cache compression with profile: auto...
  Bits: 3
  Group Size: 64

# Enable speed-optimized path (V2)
$ just kv-enable v2-speed 3
Enabling KV cache compression with profile: v2-speed...

# Enable quality-optimized path (V3)
$ just kv-enable v3-quality 3
Enabling KV cache compression with profile: v3-quality...
```

**Edge Cases**:
- **Invalid profile**: Falls back to "auto" profile.
- **Invalid bits**: Must be 2, 3, or 4 (validated by `CompressionProfile.__post_init__`).
- **TurboQuant not available**: Prints error, compression remains disabled.

---

### kv-disable

**Description**: Disable KV cache compression (revert to uncompressed KVCache).

**Syntax**:
```bash
just kv-disable
```

**Examples**:
```bash
# Disable compression
$ just kv-disable
Disabling KV cache compression...
KV cache compression disabled
```

**Edge Cases**:
- **Compression already disabled**: No-op, prints status message.
- **Server running**: Compression disabled for future prompts; existing compressed cache remains until restart.

---

### kv-list-profiles

**Description**: List all available KV cache compression profiles.

**Syntax**:
```bash
just kv-list-profiles
```

**Examples**:
```bash
$ just kv-list-profiles
Available KV Cache Profiles:
  - v2-speed: Speed-optimized path with Metal acceleration (~105% FP16 speed)
  - v3-quality: Quality-optimized path with Lloyd-Max codebook (4x+ compression)
  - auto: Automatic profile selection based on model size class
```

**Edge Cases**:
- **No profiles defined**: Shows empty list (uses defaults).
- **Custom profiles**: Displays all profiles from `kv-cache-profiles.yaml`.

---

### kv-validate

**Description**: Validate a KV cache compression profile configuration.

**Syntax**:
```bash
just kv-validate PROFILE="auto"
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `PROFILE` | string | No | Profile name to validate (default: "auto") |

**Examples**:
```bash
$ just kv-validate v2-speed
Validating KV cache profile: v2-speed...
Profile: v2-speed
Path: v2
Bits: 3
Valid: True
```

**Edge Cases**:
- **Invalid profile**: Shows "Valid: False" with error details.
- **Missing config**: Uses defaults from `kv-cache-profiles.yaml`.

---

## KV Cache Compression Overview

### What is KV Cache Compression?

KV cache compression reduces the memory footprint of the attention key-value cache during inference. For large models (120B+ parameters) on memory-constrained Apple Silicon systems (48GB), the KV cache can consume 7-8 GB of memory. Compression reduces this by 3-5x, enabling larger models or longer context windows.

### Compression Paths

| Path | Profile | Speed | Compression | Quality | Use Case |
|------|---------|-------|-------------|---------|----------|
| V2 | v2-speed | ~105% FP16 | 3.6x | Within 2% of FP16 | Speed-critical applications |
| V3 | v3-quality | ~90% FP16 | 4.1-5.5x | Within 2% of FP16 | Memory-critical applications |
| Auto | auto | Depends on selection | 3-4x | Within 2% of FP16 | General use (recommended) |

### Automatic Profile Selection (Double-Compression Rules)

The "auto" profile selects the optimal compression strategy based on model size and weight quantization:

| Model Size | Weight Bits | Recommended KV Bits | Reason |
|------------|-------------|---------------------|--------|
| ~20B | 3 (compressed) | **4-bit** | Avoid compounding noise |
| ~20B | FP16 | 3-bit | Safe, good compression |
| 100B+ | 3 (compressed) | **3-bit** | Redundancy absorbs noise |
| 100B+ | FP16 | 3-bit | Maximum compression |

**Key Finding**: 120B+ models tolerate aggressive double-compression (3-bit weights + 3-bit KV) and actually run *faster* due to reduced memory bandwidth.

### Integration with Server Lifecycle

KV cache compression integrates with the server lifecycle through environment variables:

```bash
# Start server with KV cache compression
KV_CACHE_PROFILE=v2-speed just server-start

# Or set defaults in justfile
just server-start --kv-cache-profile v2-speed
```

The server will:
1. Load model with weight quantization (if configured)
2. Process prompt with full-precision KV cache
3. Convert cache to TurboQuant format after prompt processing
4. Continue generation with compressed KV cache

### Health Endpoint

Compression status is reported via the `/health` endpoint:

```bash
curl http://localhost:8080/health | jq '.kv_cache_compression'
```

Expected output:
```json
{
  "enabled": true,
  "profile": "auto",
  "resolved_profile": "v3-quality",
  "bits": 3,
  "compression_ratio": 4.6,
  "metal_accelerated": true
}
```

### Troubleshooting

**Compression not available**:
```bash
# Install TurboQuant MLX
uv pip install turboquant-mlx-full
```

**Metal kernels fail to load**:
```bash
# Check Xcode tools
xcode-select -p
# Reinstall with verbose output
uv pip install --force-reinstall turboquant-mlx-full -v
```

**Output quality degradation (repetition/drift)**:
- Cause: Double-compression noise on small models
- Fix: Use 4-bit KV with 3-bit weights for ~20B models
- Verify: `just kv-validate <profile>`


### models-list

**Description**: List all available model profiles with metadata.

**Syntax**:
```bash
just models-list [JSON_FLAG="--json"]
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `JSON_FLAG` | flag | No | Set to `--json` for JSON output |

**Examples**:
```bash
# List profiles in human-readable format
$ just models-list
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

Total: 3 profiles
Active: nemotron-120b

# List profiles in JSON format
$ just models-list --json
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

**Edge Cases**:
- **profiles.yaml not found**: Command fails with error message suggesting to check configuration.
- **Empty profiles list**: Shows "No profiles configured" message.
- **Corrupted YAML**: Command fails with YAML parse error.

---

### model-use

**Description**: Activate a model profile for serving with optional validation.

**Syntax**:
```bash
just model-use PROFILE="" VALIDATE="true" FORCE="false"
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `PROFILE` | string | Yes | Name of the model profile to activate |
| `VALIDATE` | string | No | Set to "true" to run validation (default: true) |
| `FORCE` | string | No | Set to "true" to skip validation and force activation |

**Examples**:
```bash
# Activate a profile with validation (default)
$ just model-use nemotron-120b
Activating model profile: nemotron-120b
✓ Profile found: nemotron-120b
✓ Model path exists: ~/.cache/huggingface/hub/Nemotron-120B-48GB
✓ Key files present: config.json, model.safetensors
✓ Disk space sufficient: 120.5 GB available, 48.0 GB required
✓ Profile activated successfully

Active model: nemotron-120b

# Activate with validation disabled
$ just model-use gpt-oss-120b VALIDATE="false"

# Force activation (skip validation)
$ just model-use qwen3.5-122b FORCE="true"
```

**Edge Cases**:
- **Profile not found**: Shows error with list of available profiles.
- **Validation failure**: Shows validation errors, suggests using `--force`.
- **Disk space warning**: Activates but warns about low disk space.
- **State file locked**: Waits for lock or fails if timeout.

---

### model-status

**Description**: Display the currently active model profile.

**Syntax**:
```bash
just model-status
```

**Examples**:
```bash
# When a model is active
$ just model-status
Current Model Profile: nemotron-120b
Path: ~/.cache/huggingface/hub/Nemotron-120B-48GB
Memory: 48.0 GB
Description: Nemotron 120B optimized for 48GB Apple Silicon

# When no model is active
$ just model-status
No model profile currently active.

Use 'just models-list' to see available profiles.
Use 'just model-use <profile>' to activate a profile.
```

**Edge Cases**:
- **No active profile**: Shows helpful message with next steps.
- **State file missing**: Treats as no active profile.
- **State file corrupted**: Shows error reading state file.

---

## Troubleshooting Guide

This section covers common operational issues and their resolutions.

### Startup Failures

#### Server Fails to Start (Containerized)

**Symptoms**:
- `just start` fails with container startup error
- Podman reports image or container issues

**Root Cause**: Container image missing, build failed, or port conflict.

**Resolution Steps**:
1. Check if image exists: `podman images | grep local-mlx-server`
2. If missing, build manually: `just build`
3. Check for port conflicts: `lsof -i :8000`
4. Review container logs: `podman logs local-mlx-server`

**Prevention Tips**:
- Run `just doctor` before `just start`
- Ensure Containerfile is up to date
- Keep Podman updated

#### Server Fails to Start (Native)

**Symptoms**:
- `just run` fails with Python errors
- mlx_lm.server crashes during startup

**Root Cause**: Missing dependencies, invalid MODEL_PATH, or port conflict.

**Resolution Steps**:
1. Verify environment: `just doctor`
2. Check model path exists: `ls -la $MODEL_PATH`
3. Check port availability: `lsof -i :8000`
4. Review server logs for specific errors

**Prevention Tips**:
- Run `just init` after pulling new changes
- Use absolute paths for MODEL_PATH
- Test with `just doctor` before starting

#### Model Load Failures

**Symptoms**:
- Server starts but fails to load model
- Errors about missing model files or invalid format

**Root Cause**: Invalid model path, corrupted model files, or incompatible model format.

**Related Recipes**:
- [`just run`](#run) - Server startup with MODEL_PATH
- [`just doctor`](#doctor) - Checks model path validity

**Resolution Steps**:
1. Verify model directory structure (should have `config.json`, `model.safetensors`, etc.)
2. Check model compatibility with MLX
3. Re-download model if files are corrupted
4. Ensure sufficient disk space

**Prevention Tips**:
- Use verified model sources
- Keep model files in authorized directories
- Document model source and version

---

#### Container Runtime Issues

**Symptoms**:
- Podman daemon not running
- Container commands fail with connection errors
- `just start` fails with "Cannot connect to Podman daemon"

**Root Cause**: Podman service not running or misconfigured.

**Related Recipes**:
- [`just start`](#start) - Container startup
- [`just status`](#status) - Check container status

**Resolution Steps**:
1. Start Podman service: `podman machine start` (if using Podman Machine)
2. Check Podman status: `podman info`
3. Restart Podman daemon if needed
4. Verify Podman installation: `podman --version`

**Prevention Tips**:
- Ensure Podman starts on system boot
- Monitor Podman daemon health
- Keep Podman updated

---

#### Model Path Permission Issues

**Symptoms**:
- Server fails to read model files
- Permission denied errors when loading model
- `just run` fails with "Permission denied"

**Root Cause**: Incorrect file permissions on model directory or files.

**Related Recipes**:
- [`just run`](#run) - Server startup with MODEL_PATH
- [`just doctor`](#doctor) - Checks model path validity

**Resolution Steps**:
1. Check permissions: `ls -la $MODEL_PATH`
2. Fix directory permissions: `chmod -R 755 $MODEL_PATH`
3. Fix file ownership: `chown -R $(whoami) $MODEL_PATH`
4. Verify access: `cat $MODEL_PATH/config.json`

**Prevention Tips**:
- Set correct permissions when downloading models
- Use authorized directories per AGENTS.md
- Document permission requirements for model paths

---

### Memory Issues

#### Out of Memory (OOM) Errors

**Symptoms**:
- Server crashes during model load with memory errors
- macOS shows memory pressure warning

**Root Cause**: Model requires more memory than available, especially for 120B+ models on memory-constrained systems.

**Resolution Steps**:
1. Use more aggressive quantization (lower expert bit-width)
2. Reduce context length (MAX_TOKENS)
3. Enable KV cache compression
4. Close other memory-intensive applications
5. Switch to a lower memory tier profile (see [Model Profile Decision Tree](#model-profile-decision-tree))

**Prevention Tips**:
- Check system memory before starting: `system_profiler SPHardwareDataType | grep "Memory:"`
- Use appropriate model profile for your memory tier
- Monitor memory usage with `top` or Activity Monitor

#### KV Cache Overflow

**Symptoms**:
- Server runs out of memory during long conversations
- Gradual slowdown and eventual crash

**Root Cause**: KV cache grows with context length, exceeding available memory.

**Resolution Steps**:
1. Reduce MAX_TOKENS setting
2. Enable KV cache compression in quantization config
3. Use shorter conversation contexts
4. Restart server periodically for long sessions

**Prevention Tips**:
- Set MAX_TOKENS based on your memory tier (see [Model Profile Decision Tree](#model-profile-decision-tree))
- Monitor KV cache usage in server logs
- Use per-path hybrid quantization with KV cache compression

#### Quantization Failures

**Symptoms**:
- Errors during model quantization
- Server starts but generates poor quality output

**Root Cause**: Invalid quantization configuration or incompatible model architecture.

**Resolution Steps**:
1. Verify quantization config in model profile
2. Check model architecture compatibility with TurboQuant
3. Revert to default quantization settings
4. Test with known working configuration

**Prevention Tips**:
- Document working quantization settings per model
- Test quantization changes in isolation
- Keep backup of known-good configurations

---

### Port Conflicts

**Symptoms**:
- Server fails to bind to port 8000 (or configured port)
- Error: "Address already in use"

**Root Cause**: Another process is using the configured port.

**Resolution Steps**:
1. Identify conflicting process: `lsof -i :8000`
2. Stop the conflicting process: `kill <PID>` or `just stop` if it's an old server instance
3. Use different port: `PORT=8080 just start`
4. For persistent conflicts, identify and reconfigure the other service

**Prevention Tips**:
- Run `just doctor` before starting server
- Document custom port configurations
- Use `lsof -i :8000` in monitoring scripts

---

## Model Profile Decision Tree

This section helps operators select the correct model profile based on system memory (48GB, 64GB, or 96GB tiers) for optimal performance on Apple Silicon.

### Decision Logic

```
START: Check your system memory
├── Run: system_profiler SPHardwareDataType | grep "Memory:"
│
├── 48GB tier (e.g., M2 Max 48GB)
│   ├── Profile: Low Memory
│   ├── Expected: ~15 tok/s, 2K context, ~42GB used
│   └── Use: just run with default or explicit low-memory settings
│
├── 64GB tier (e.g., M2 Ultra 64GB)
│   ├── Profile: Balanced
│   ├── Expected: ~22 tok/s, 4K context, ~56GB used
│   └── Use: just run with balanced settings
│
├── 96GB tier (e.g., M2 Ultra 96GB)
│   ├── Profile: High Performance
│   ├── Expected: ~30 tok/s, 8K context, ~80GB used
│   └── Use: just run with high-performance settings
│
└── Between tiers? (e.g., 56GB, 72GB)
    └── RULE: Always use LOWER tier for stability
        ├── 56GB → Use 48GB profile
        └── 72GB → Use 64GB profile
```

### Memory Check Command

```bash
# Check your system memory
system_profiler SPHardwareDataType | grep "Memory:"
# Example output: Memory: 64 GB
```

### Profile Details

#### 48GB Tier Profile

**Target Systems**: M2 Max 48GB, similar configurations

**Performance Metrics**:
- Tokens per second: ~15
- Context length: 2K (2048 tokens)
- Memory used: ~42GB

**Quantization Configuration**:
- Weight compression: 2-bit experts, 4-bit attention
- KV cache: 4-bit compression enabled
- Per-path hybrid: Aggressive expert quantization

**Just Recipe Usage**:
```bash
# Use default settings (optimized for 48GB)
just run

# Or explicitly set lower context
MAX_TOKENS=2048 just run
```

---

#### 64GB Tier Profile

**Target Systems**: M2 Ultra 64GB, M3 Max 64GB

**Performance Metrics**:
- Tokens per second: ~22
- Context length: 4K (4096 tokens)
- Memory used: ~56GB

**Quantization Configuration**:
- Weight compression: 2-bit experts, 4-bit attention
- KV cache: 4-bit compression enabled
- Per-path hybrid: Balanced quantization

**Just Recipe Usage**:
```bash
# Default settings work well for 64GB
just run

# Or explicitly set context
MAX_TOKENS=4096 just run
```

---

#### 96GB Tier Profile

**Target Systems**: M2 Ultra 96GB, M3 Max 96GB

**Performance Metrics**:
- Tokens per second: ~30
- Context length: 8K (8192 tokens)
- Memory used: ~80GB

**Quantization Configuration**:
- Weight compression: 3-bit experts, 4-bit attention
- KV cache: 4-bit compression enabled
- Per-path hybrid: Quality-optimized quantization

**Just Recipe Usage**:
```bash
# Use higher context for 96GB systems
MAX_TOKENS=8192 just run

# Or with custom model path
MODEL_PATH=./models/nemotron-120b-q3 MAX_TOKENS=8192 just run
```

---

## Developer Guidelines

This section provides guidelines for contributors adding or modifying `just` recipes.

### Recipe Naming Conventions

- Use **kebab-case** for recipe names: `my-new-recipe` (not `my_new_recipe` or `myNewRecipe`)
- Use **descriptive verbs**: `start-server`, `check-status`, `run-tests`
- Be **concise but clear**: `lint` not `run-code-linting-checks`

### Justfile Contribution Standards

When adding a new recipe to `justfile`:

1. **Add description comment** above the recipe:
   ```bash
   # Run linting and formatting
   lint:
       uv run ruff check . --fix
       uv run ruff format .
   ```

2. **Use environment variables** for configurable values:
   ```bash
   MODEL_PATH := "./models"
   
   run:
       uv run python -m mlx_lm.server --model {{MODEL_PATH}}
   ```

3. **Document the recipe** in OPERATIONS.md following the standard format:
   - Syntax
   - Environment variables (table)
   - Examples (at least one)
   - Edge cases

4. **Test your recipe** with `just verify` before committing

### Testing Requirements for New Recipes

- Recipe must execute without errors in default configuration
- Recipe must handle missing dependencies gracefully (with helpful error messages)
- Recipe must be documented in OPERATIONS.md
- Run `just verify` to ensure no regressions

### Documentation Standards

- Use "just recipe" as the canonical terminology (not "just command", "recipe", or "command")
- Include file paths as clickable links: [`justfile`](justfile)
- Follow markdown best practices (tables, code blocks, headers)
- Provide working examples with expected output
- Document edge cases and error conditions

---

## Related Documentation

- [README](README.md) - Project overview and navigation index
- [Agent Rules](AGENTS.md) - Operational charter and agent guidelines
- [Governance](GOVERNANCE.md) - Project constitution and standards
- [Contributing](CONTRIBUTING.md) - Contribution guidelines and development workflow
- [Security Validation](docs/security-validation.md) - Security patterns and helpers

## Quantization Management (Spec 007)

The following just recipes are available for managing per-path hybrid quantization:

### List Available Quantization Profiles

```bash
just quant-list
```

Lists all available quantization profiles from `scripts/wrapper-config/profiles.yaml`.

### Validate a Quantization Profile

```bash
just quant-validate <profile>
```

Validates a quantization profile for syntax and compatibility. Exit codes: 0 (success), 1 (validation failed).

### Apply Quantization to a Model

```bash
just quant-apply <model> <profile>
```

Applies a quantization profile to a model. Validates profile, detects model architecture, applies per-path quantization, and updates `.active-model`.

### Check Quantization Status

```bash
just quant-status
```

Displays current quantization configuration for the active model, including profile, bit-widths, and model architecture details.

### Run Lloyd-Max Calibration

```bash
just quant-calibrate <dataset> <output>
```

Runs Lloyd-Max calibration with provided dataset to generate optimized codebooks for better quantization accuracy.

### Using Quantization with Model Management

```bash
# Activate a model profile with quantization
uv run python scripts/model-management.py use <profile> --quant-profile tq3a-tq2e-g32

# Or use environment variable
export MLX_QUANT_PROFILE=tq3a-tq2e-g32
just mlx-start
```

### Health Endpoint

The health endpoint (`/health`) now includes quantization status:

```json
{
  "quantization": {
    "profile": "tq3a-tq2e-g32",
    "attention_bits": 3,
    "expert_bits": 2,
    "group_size": 32,
    "model_architecture": "Nemotron-3-Super-120B-A12B",
    "is_moe": true,
    "expert_count": 12,
    "active_params": 12000000000,
    "total_params": 120000000000
  }
}
```
