# CLI Interface Contract: MLX Server Wrapper

**Date**: 2026-05-11  
**Feature**: 004-mlx-server-wrapper  
**Status**: Complete

## Contract Format

The MLX server wrapper provides a CLI interface using Click with subcommands for server lifecycle management.

---

## Primary CLI Entry Point

**Command**: `python scripts/mlx-wrapper.py` or `mlx-wrapper` (if installed)

**Global Options**:
- `--config PATH`: Path to YAML configuration file (default: `scripts/wrapper-config/profiles.yaml`)
- `--verbose`: Enable verbose/debug logging
- `--help`: Show help message

---

## Subcommand: start

Start MLX server with specified profile.

**Contract**:
```bash
mlx-wrapper start --profile PROFILE_NAME [--port PORT] [--host HOST]
```

**Arguments**:
- `--profile TEXT` (required): Model profile name as defined in profiles.yaml
- `--port INTEGER` (optional): Server port (overrides profile default, default: 8080)
- `--host TEXT` (optional): Server host (overrides profile default, default: "127.0.0.1")
- `--preset TEXT` (optional): Apply memory optimization preset (e.g., "120b-extreme")

**Behavior**:
1. Validate profile exists in configuration
2. Check available memory against profile/preset requirements
3. Load model profile and apply quantization settings
4. Start mlx_lm.server as subprocess with configured arguments
5. Wait for server ready (poll `/v1/models` endpoint)
6. Output success message with server URL and health endpoint

**Exit Codes**:
- `0`: Server started successfully
- `1`: Invalid profile or configuration error
- `2`: Insufficient memory
- `3`: Server failed to start within timeout
- `4`: Port already in use

**Example**:
```bash
$ mlx-wrapper start --profile 120b-balanced
[INFO] Loading profile: 120b-balanced
[INFO] Model: Nemotron-120B
[INFO] Checking memory... 48.2GB available, 45GB required ✓
[INFO] Starting server on http://127.0.0.1:8080
[INFO] Waiting for model load... (this may take 3-5 minutes)
[PROGRESS] Loading model... 45%
[PROGRESS] Loading model... 87%
[SUCCESS] Server ready at http://127.0.0.1:8080
[INFO] Health endpoint: http://127.0.0.1:8080/health
```

---

## Subcommand: stop

Stop running MLX server gracefully.

**Contract**:
```bash
mlx-wrapper stop [--force] [--timeout SECONDS]
```

**Arguments**:
- `--force`: Force kill if graceful shutdown fails
- `--timeout INTEGER` (default: 30): Seconds to wait for graceful shutdown

**Behavior**:
1. Find running mlx_lm.server process (via PID file or port detection)
2. Send SIGTERM for graceful shutdown
3. Wait up to timeout for process to exit
4. If `--force`, send SIGKILL after timeout
5. Clean up PID file and temporary resources

**Exit Codes**:
- `0`: Server stopped successfully
- `1`: No running server found
- `2`: Force kill required (with `--force`)
- `3`: Timeout waiting for shutdown

---

## Subcommand: status

Check server running status.

**Contract**:
```bash
mlx-wrapper status [--json]
```

**Arguments**:
- `--json`: Output in JSON format (for programmatic use)

**Behavior**:
1. Check if mlx_lm.server process is running
2. Query `/v1/models` endpoint for model status
3. Return status: "running", "stopped", "degraded"

**Output** (human-readable):
```
Server Status: running
Model: Nemotron-120B
Profile: 120b-balanced
Uptime: 2h 34m
Memory: 45.2GB / 48GB
Active Requests: 0
```

**Output** (JSON):
```json
{
  "status": "running",
  "model": "Nemotron-120B",
  "profile": "120b-balanced",
  "uptime_seconds": 9240,
  "memory_usage_gb": 45.2,
  "memory_limit_gb": 48,
  "active_requests": 0
}
```

---

## Subcommand: health

Detailed health check with system metrics.

**Contract**:
```bash
mlx-wrapper health [--json] [--wait] [--timeout SECONDS]
```

**Arguments**:
- `--json`: Output in JSON format
- `--wait`: Wait for server to become healthy
- `--timeout INTEGER` (default: 60): Max seconds to wait if `--wait` specified

**Behavior**:
1. Query wrapper health endpoint (`/health`)
2. Include system metrics: memory, CPU, disk
3. Check model loading progress if initializing
4. Report active request count

**Health Status Levels**:
- `healthy`: Server ready, model loaded, accepting requests
- `initializing`: Server starting, model loading in progress
- `degraded`: Server running but with issues (high memory, errors)
- `down`: Server not responding

**Output** (JSON):
```json
{
  "status": "healthy",
  "model": "Nemotron-120B",
  "model_loaded": true,
  "load_progress_pct": 100,
  "memory_usage_gb": 45.2,
  "memory_limit_gb": 48,
  "uptime_seconds": 9240,
  "active_requests": 0,
  "system": {
    "cpu_percent": 12.5,
    "memory_available_gb": 2.8,
    "disk_free_gb": 120.5
  }
}
```

---

## Subcommand: list-profiles

List available model profiles.

**Contract**:
```bash
mlx-wrapper list-profiles [--json]
```

**Output** (human-readable):
```
Available Profiles:
  - 120b-balanced (Nemotron-120B, hybrid quantization)
  - 120b-extreme (Nemotron-120B, aggressive compression)
  - 70b-standard (Llama-70B, 4-bit uniform)
```

---

## Subcommand: list-presets

List available memory optimization presets.

**Contract**:
```bash
mlx-wrapper list-presets [--json]
```

**Output** (human-readable):
```
Available Presets:
  - 120b-extreme (target: 45GB, model: 120B+)
  - 120b-balanced (target: 48GB, model: 120B+)
```

---

## Error Handling

All subcommands must:
1. Catch exceptions and display user-friendly error messages
2. Log full traceback to log file in verbose mode
3. Return appropriate exit codes
4. Validate inputs before attempting operations

**Error Message Format**:
```
[ERROR] <brief description>
<optional details or suggestion>
```

Example:
```
[ERROR] Profile 'invalid-name' not found
Available profiles: 120b-balanced, 120b-extreme, 70b-standard
Use: mlx-wrapper list-profiles
```
