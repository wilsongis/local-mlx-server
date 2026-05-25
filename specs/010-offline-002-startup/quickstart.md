# Quickstart: Startup Preflight and Degraded Mode

**Feature**: 010-offline-002-startup | **Date**: 2026-05-24

## Overview

This feature adds automatic preflight checks before starting the MLX server, with support for degraded mode when non-critical checks fail. This prevents failed startups and wasted system resources on memory-constrained Apple Silicon systems.

## Prerequisites

- Apple Silicon Mac (M1/M2/M3) with 48GB+ unified memory for 120B+ models
- Python 3.11+ with `uv` package manager
- Existing `local-mlx-server` project setup (`just init` completed)
- Model downloaded to `./models/` directory

## Quick Start

### 1. Run Preflight Checks Manually

```bash
# Check system readiness without starting server
just preflight

# Or with explicit model path
just preflight MODEL_PATH=./models/my-120b-model
```

Expected output:
```
Running preflight checks...
✓ Memory budget: 64GB available (48GB required for 120B+ models)
✓ Wired memory limit: 8GB (within acceptable range)
✓ Disk space: 100GB available (50GB required)
✓ Dependencies: mlx-lm 0.19.0, psutil 5.9.0
✓ Profile fallback: Using 'tq3a-tq2e-g32' for 120B+ model
Result: READY - System ready for server startup
```

### 2. Start Server with Preflight (Automatic)

```bash
# Start server - preflight runs automatically before startup
just run

# Or with containerized deployment
just start
```

If preflight fails critically:
```
Running preflight checks...
✓ Memory budget: 64GB available
✗ Wired memory limit: 15GB (exceeds 12GB limit)
✗ Dependencies: mlx-lm not found

ERROR: Critical preflight checks failed. Server startup blocked.
Fix the issues above and try again.
```

If non-critical checks fail (degraded mode):
```
Running preflight checks...
✓ Memory budget: 64GB available
✓ Wired memory limit: 8GB
✓ Disk space: 100GB available
✗ TurboQuant: Not available (optional)
✗ KV cache compression: Not available (optional)

WARNING: Entering degraded mode.
Disabled features: TurboQuant, KV cache compression
Server starting with standard 4-bit quantization...
```

### 3. Check Preflight Status via Health Endpoint

After server starts (either normally or in degraded mode):

```bash
# Standard health check
curl http://127.0.0.1:8000/health

# Extended preflight status
curl http://127.0.0.1:8000/health/preflight
```

Degraded mode health response:
```json
{
  "status": "degraded",
  "preflight": {
    "last_check": "2026-05-24T18:00:00Z",
    "overall_status": "degraded",
    "checks": [
      {"name": "memory_budget", "status": "pass", "type": "critical"},
      {"name": "turboquant", "status": "fail", "type": "non_critical"}
    ]
  },
  "degraded_mode": {
    "active": true,
    "disabled_features": ["turboquant", "kv_cache_compression"],
    "fallback_profile": "4bit-standard"
  }
}
```

### 4. View Degraded Mode in Admin GUI

1. Open Admin GUI: `just gui` or navigate to `http://127.0.0.1:8080`
2. Degraded mode banner appears at top if active
3. Status page shows disabled features and fallback profile

## Configuration

Edit `scripts/wrapper-config/preflight-config.yaml` to customize thresholds:

```yaml
# Memory thresholds (in GB)
memory:
  critical_120b: 48      # Minimum for TurboQuant 120B+
  standard_120b: 64      # Minimum for standard 4-bit 120B
  warning_threshold: 56   # Warning below this

# Wired memory limit (in GB)
wired_limit: 12

# Disk space (in GB)
disk_space:
  min_required: 50
  check_path: "."  # Path to check

# Profile fallback chain
profile_fallback:
  - "user_specified"      # Highest priority
  - "model_detected"
  - "memory_based"
  - "120b-balanced"       # Safe default
```

## Troubleshooting

### Server won't start - "Critical preflight checks failed"

1. Check memory: `uv run python -c "import psutil; print(f'Memory: {psutil.virtual_memory().total / 1e9:.1f}GB')"`
2. Verify MLX: `uv run python -c "import mlx_lm; print(mlx_lm.__version__)"`
3. Check model path: `ls -la ./models/`

### Server in degraded mode unexpectedly

1. Check preflight details: `curl http://127.0.0.1:8000/health/preflight`
2. Review logs: `tail -f logs/server.log`
3. Install missing deps: `uv pip install turboquant-mlx` (if available)

### Performance issues in degraded mode

- Degraded mode uses standard 4-bit quantization (no TurboQuant optimization)
- Consider upgrading system memory or freeing wired memory
- Check Activity Monitor for memory pressure

## Testing

```bash
# Run unit tests for preflight checks
uv run pytest tests/test_preflight.py -v

# Run integration test (requires model)
uv run pytest tests/test_preflight_integration.py -v

# Test preflight check logic
uv run python scripts/preflight/checker.py --dry-run
```

## Next Steps

- Review [`plan.md`](plan.md) for implementation details
- Check [`data-model.md`](data-model.md) for entity definitions
- See [`contracts/preflight-interface.md`](contracts/preflight-interface.md) for interface specs
