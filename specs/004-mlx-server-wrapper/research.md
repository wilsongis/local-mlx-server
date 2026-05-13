# Research: MLX Server Wrapper

**Date**: 2026-05-11  
**Feature**: 004-mlx-server-wrapper  
**Status**: Complete

## Research Questions & Findings

### 1. mlx_lm.server Startup and Shutdown Workflow

**Decision**: Use subprocess management with signal handling for graceful startup/shutdown of mlx_lm.server.

**Rationale**: The wrapper needs to manage the mlx_lm.server process lifecycle while adding health monitoring and graceful shutdown capabilities.

**Findings**:
- `mlx_lm.server` is a FastAPI/Starlette-based server with OpenAI-compatible endpoints
- Server accepts arguments: `--model`, `--host`, `--port`, `--temperature`, `--max-tokens`, etc.
- Process can be managed via Python's `subprocess.Popen` with PID tracking
- Graceful shutdown requires SIGTERM forwarding, waiting for active requests to complete
- Health checks can use the `/v1/models` endpoint or custom health endpoint
- Server startup time for 120B+ models can exceed 3-5 minutes on 48GB systems

**Implementation Approach**:
```python
import subprocess
import signal
import time

class MLXServerManager:
    def __init__(self, model_path: str, port: int = 8080):
        self.process = None
        self.model_path = model_path
        self.port = port
    
    def start(self):
        cmd = ["python", "-m", "mlx_lm.server", 
               "--model", self.model_path, 
               "--port", str(self.port)]
        self.process = subprocess.Popen(cmd)
        return self._wait_for_ready(timeout=300)  # 5 min for 120B+
    
    def stop(self):
        if self.process:
            self.process.send_signal(signal.SIGTERM)
            self.process.wait(timeout=30)
    
    def health_check(self) -> dict:
        # Query /v1/models endpoint
        import requests
        try:
            resp = requests.get(f"http://localhost:{self.port}/v1/models", timeout=1)
            return {"status": "healthy" if resp.ok else "degraded", "code": resp.status_code}
        except:
            return {"status": "down"}
```

**Alternatives considered**:
- Using mlx_lm.server as a library import → Rejected: server is designed as CLI tool, not library
- Daemonizing with systemd/launchd → Rejected: violates portability, overkill for local inference

---

### 2. Model Profile Selection with Per-Path Hybrid Quantization

**Decision**: Use YAML-based profile definitions with support for per-layer quantization specifications compatible with TurboQuant.

**Rationale**: YAML provides human-readable configuration; per-path quantization is critical for 120B+ models where different layers benefit from different quantization strategies.

**Findings**:
- Hybrid quantization allows different bits/precision per model path (e.g., attention layers at 8-bit, FFN at 4-bit)
- TurboQuant supports specifying quantization config per layer or layer group
- mlx-lm supports `--quantize` argument with type specification
- Per-path config requires mapping layer names/paths to quantization types
- Profile should specify: model path, quantization config, KV cache settings, inference args

**Profile YAML Structure**:
```yaml
profiles:
  - name: "120b-balanced"
    model_path: "~/.cache/huggingface/hub/Nemotron-120B"
    quantization:
      type: "hybrid"
      paths:
        - pattern: "attention.*"  # regex or glob
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
      max_tokens: 4096
```

**Alternatives considered**:
- JSON configuration → Rejected: less readable for complex nested structures
- TOML configuration → Considered but YAML more common in ML ecosystem
- Hardcoded profiles in Python → Rejected: not user-extensible

---

### 3. Memory Optimization Presets for 120B+ Models on Apple Silicon

**Decision**: Create named presets targeting specific memory constraints with automatic argument adjustment.

**Rationale**: 120B+ models require careful memory management on 48GB systems; presets reduce configuration errors.

**Findings**:
- 120B model at 4-bit: ~60GB (too large for 48GB without optimization)
- With hybrid quantization (8-bit attention, 4-bit FFN): ~48GB achievable
- KV cache compression (4-bit) saves 2-4GB for long contexts
- Reducing context length from 4096 to 2048 saves ~2GB
- Batch size of 1 is mandatory for 120B+ on 48GB
- psutil can check available memory before startup

**Preset Definitions**:
```yaml
presets:
  - name: "120b-extreme"
    target_memory_gb: 45
    model_size_class: "120B+"
    quantization: "hybrid-aggressive"  # 4-bit primary, 8-bit attention only
    kv_cache_bits: 4
    max_context_length: 1024
    batch_size: 1
    description: "Minimum viable config for 120B on 48GB"
    
  - name: "120b-balanced"
    target_memory_gb: 48
    model_size_class: "120B+"
    quantization: "hybrid-balanced"  # 8-bit attention, 4-bit FFN
    kv_cache_bits: 4
    max_context_length: 2048
    batch_size: 1
    description: "Balanced performance/memory for 120B on 48GB"
```

**Memory Check Implementation**:
```python
import psutil

def check_memory_available(required_gb: float) -> tuple[bool, str]:
    mem = psutil.virtual_memory()
    available_gb = mem.available / (1024**3)
    if available_gb < required_gb:
        return False, f"Only {available_gb:.1f}GB available, {required_gb}GB required"
    return True, "OK"
```

**Alternatives considered**:
- Dynamic memory adjustment at runtime → Rejected: mlx-lm doesn't support dynamic reloading
- Swap-based serving → Rejected: terrible performance on Apple Silicon

---

### 4. CLI Wrapper Design with Click

**Decision**: Use Click for CLI interface with subcommands (start, stop, status, health).

**Rationale**: Click provides decorator-based CLI creation, excellent help text, and subcommand support matching the requirement for a single wrapper script with subcommands.

**Findings**:
- Click decorators: `@click.group()`, `@click.command()`
- Subcommands map to just recipe targets
- Options can load from YAML config with `--profile` flag
- Colorized output with `click.secho()` for status messages
- Progress bars with `click.progressbar()` for model loading

**CLI Structure**:
```python
import click
import yaml

@click.group()
@click.option('--config', default='scripts/wrapper-config/profiles.yaml')
@click.pass_context
def cli(ctx, config):
    ctx.ensure_object(dict)
    ctx.obj['config'] = yaml.safe_load(open(config))

@cli.command()
@click.option('--profile', required=True, help='Model profile name')
@click.pass_context
def start(ctx, profile):
    """Start MLX server with specified profile"""
    config = ctx.obj['config']
    # Load profile, start server
    click.secho(f"Starting server with profile: {profile}", fg='green')

@cli.command()
def status():
    """Check server status"""
    # Query health endpoint
    click.echo("Server status: running")
```

**Alternatives considered**:
- argparse → Rejected: more verbose, less intuitive for subcommands
- typer (Click wrapper) → Considered but adds dependency; Click is sufficient

---

### 5. Integration with Just Command Recipes

**Decision**: Add wrapper-specific recipes to justfile that call the Python wrapper script.

**Rationale**: Maintains operational consistency per Principle IV (Just Command Bridge) while providing the enhanced wrapper functionality.

**Findings**:
- justfile recipes should wrap `python scripts/mlx-wrapper.py <subcommand>`
- Recipes: `mlx-start`, `mlx-stop`, `mlx-status`, `mlx-health`
- Pass profile/preset as just arguments: `just mlx-start 120b-balanced`
- Maintain backward compatibility with existing just recipes

**Justfile Additions**:
```make
# MLX Server Wrapper Commands
mlx-start PROFILE="120b-balanced":
    python scripts/mlx-wrapper.py start --profile {{PROFILE}}

mlx-stop:
    python scripts/mlx-wrapper.py stop

mlx-status:
    python scripts/mlx-wrapper.py status

mlx-health:
    python scripts/mlx-wrapper.py health
```

**Alternatives considered**:
- Replacing existing just recipes → Rejected: need backward compatibility
- Separate justfile for wrapper → Rejected: fragments operational interface

---

### 6. Health Check Endpoint Design

**Decision**: Implement wrapper-level health check that aggregates mlx_lm.server status with system metrics.

**Rationale**: Basic `/v1/models` check is insufficient; need memory usage, model loading progress, and request queue depth.

**Findings**:
- mlx_lm.server doesn't expose detailed health endpoint natively
- Wrapper can proxy requests and add health metadata
- Health status levels: `initializing`, `ready`, `degraded`, `down`
- Include: model load progress, memory usage, active requests, uptime
- Health endpoint: `GET /health` on wrapper (not mlx server)

**Health Response Format**:
```json
{
  "status": "ready",
  "model": "Nemotron-120B",
  "model_loaded": true,
  "memory_usage_gb": 45.2,
  "memory_limit_gb": 48,
  "uptime_seconds": 3600,
  "active_requests": 0,
  "load_progress_pct": 100
}
```

**Implementation**: Wrapper runs lightweight HTTP server on separate port for health endpoint, or uses same port with `/health` path (if not conflicting with mlx_lm.server).

**Alternatives considered**:
- Relying solely on mlx_lm.server `/v1/models` → Insufficient for operational needs
- Separate monitoring daemon → Overkill; wrapper can provide basic health endpoint

---

## Summary of Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Process management | subprocess.Popen with signal handling | Standard Python approach, cross-platform |
| Profile config format | YAML | Human-readable, ML ecosystem standard |
| CLI framework | Click | Decorator-based, excellent subcommand support |
| Health checks | Wrapper-level endpoint with aggregation | mlx_lm.server lacks detailed health info |
| Memory checking | psutil | Cross-platform, mature library |
| Just integration | Add wrapper recipes alongside existing | Maintains Principle IV compliance |

All NEEDS CLARIFICATION resolved. Proceeding to Phase 1.
