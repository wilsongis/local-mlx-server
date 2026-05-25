# Local MLX Server

## Quick Navigation by Persona

### 🖥️ Operators (Run the Server)
- [Operations Guide](OPERATIONS.md) - Server startup, `just` recipes, monitoring, and troubleshooting

### 👩‍💻 Contributors (Add Code/Docs)
- [Contributing Guide](CONTRIBUTING.md) - Setup, development workflow, testing, and PR process
- [Agent Rules](AGENTS.md) - Operational charter, `/speckit.*` commands, and agent guidelines

### 🛡️ Maintainers (Governance)
- [Governance](GOVERNANCE.md) - Constitution, documentation standards, release processes, and project policies

## Project Overview

Local MLX Server is an isolated inference infrastructure repository for running very large Mixture-of-Experts LLMs locally on Apple Silicon, with a practical focus on 120B+ class models such as GPT-OSS and Nemotron variants.

The project exists to solve one bottleneck: memory pressure from both model weights and runtime KV cache when context length grows.

## The Core Problem

Running 120B+ MoE models locally is usually blocked by unified memory limits, even when only a subset of experts is active per token.

- MoE models still require all expert weights resident in memory.
- Standard formats can fail to fit practical hardware tiers.
- KV cache scales with context length and can consume multiple additional GB at long prompts.
- This is especially critical on Apple Silicon machines in the 64 GB and 96 GB unified memory tiers, where memory headroom directly determines whether long-context inference is possible.

## Technical Solution: TurboQuant Methodology Adapted to MLX

This repository centers on the TurboQuant-MLX approach described in the research notes under `docs/research`.

### 1) Weight Compression for MoE

- Use Hadamard-based rotation to Gaussianize weight distributions.
- Apply Lloyd-Max style codebook quantization to match Gaussian-like post-rotation distributions.
- Extend quantization to MoE expert-heavy architectures, including packed expert representations and efficient MoE kernel paths.

### 2) Per-Path Hybrid Quantization

A key capability is per-path bit allocation instead of one uniform bit-width:

- Attention path kept at higher precision (example: 3-bit attention).
- Expert path compressed more aggressively (example: 2-bit experts).
- Grouped quantization settings (example: group size 32) used to hit memory targets.

Why this matters:

- Attention is more error-sensitive during autoregressive decoding.
- Expert parameters dominate total size, so lowering expert bit-width drives major memory reduction.
- This hybrid split enabled practical 120B deployment on tighter memory budgets in the referenced experiments.

### 3) KV Cache Compression

TurboQuant is also applied to KV cache storage:

- On-the-fly KV compression using rotation + codebook quantization.
- Approximately 4x to 4.6x KV cache compression in reported configurations.
- Materially lowers runtime memory at long context lengths.
- For very large models, reduced memory traffic can also improve throughput.
## What This Repository Is Building Toward

The infrastructure goal is explicit:

- A standalone, lightweight inference hub.
- Dependency and environment management through `uv`.
- A localized OpenAI-compatible API endpoint powered by `mlx_lm.server`.
- Reliable local serving for agentic coding tools and adjacent local automation systems.

This repository is not intended to become an application monolith. It is the model-serving backbone.

---

## MLX Server Wrapper

The MLX Server Wrapper (`scripts/mlx_wrapper.py`) provides a unified CLI interface for managing `mlx_lm.server` instances with health monitoring, model profile selection, and memory-optimized presets for 120B+ models.

#
## Per-Path Hybrid Quantization (Spec 007)

This repository now supports per-path hybrid quantization for MLX models on Apple Silicon, enabling different bit-widths for attention versus expert layers (e.g., tq3a-tq2e g32). This feature supports latent-MoE architectures like Nemotron-3-Super-120B-A12B and provides Lloyd-Max codebook calibration for better quantization accuracy.

### Key Features

- **Per-Path Quantization**: Configure different bit-widths for attention (3-bit) and expert (2-bit) layers
- **MoE Support**: Automatic detection and optimization for mixture-of-experts architectures
- **Lloyd-Max Calibration**: Optional codebook calibration for improved quantization accuracy
- **Just Recipes**: Easy-to-use commands for quantization management (Available Quantization Profiles:
  - tq3a-tq2e-g32 (attention: 3-bit, expert: 2-bit, group: 32)
  - tq4a-tq4e-g32 (attention: 4-bit, expert: 4-bit, group: 32), Usage: just quant-apply <model> <profile>, etc.)
- **Health Endpoint**: Extended  endpoint with quantization status

### Quick Start

1. List available quantization profiles:
   Available Quantization Profiles:
  - tq3a-tq2e-g32 (attention: 3-bit, expert: 2-bit, group: 32)
  - tq4a-tq4e-g32 (attention: 4-bit, expert: 4-bit, group: 32)

2. Apply quantization to a model:
   Applying quantization profile 'tq3a-tq2e-g32' to model '/Users/wilsonm/.cache/huggingface/hub/Nemotron-3-Super-120B-A12B'...

3. Check quantization status:
   Quantization Status:
{
  "profile": null,
  "attention_bits": null,
  "expert_bits": null,
  "group_size": null,
  "model_architecture": null,
  "is_moe": false,
  "expert_count": 0,
  "active_params": null,
  "total_params": null
}

For detailed documentation, see [OPERATIONS.md](OPERATIONS.md#quantization-management-spec-007).

## KV Cache Compression (Spec 008)

This repository now supports KV cache compression for MLX-based inference on Apple Silicon, reducing KV cache memory usage by 3-5x to enable 120B+ models on 48GB systems.

### Key Features

- **Two Compression Paths**: Speed-optimized (V2, ~105% FP16 speed) and quality-optimized (V3, 4x+ compression)
- **Automatic Profile Selection**: Based on model size class and weight quantization (double-compression rules)
- **Double-Compression Support**: Combined weight + KV cache compression with tolerance rules
- **Just Recipes**: Easy-to-use commands for compression management:
  - `just kv-status` - Show compression status
  - `just kv-enable [profile] [bits]` - Enable compression (auto/v2-speed/v3-quality)
  - `just kv-disable` - Disable compression
  - `just kv-list-profiles` - List available profiles
- **Health Endpoint**: Compression status reported via `/health` endpoint
- **Fallback Support**: Graceful degradation to uncompressed cache on initialization failure

### Compression Paths

| Path | Profile | Speed | Compression | Quality | Use Case |
|------|---------|-------|-------------|---------|----------|
| V2 | v2-speed | ~105% FP16 | 3.6x | Within 2% of FP16 | Speed-critical applications |
| V3 | v3-quality | ~90% FP16 | 4.1-5.5x | Within 2% of FP16 | Memory-critical applications |
| Auto | auto | Depends on selection | 3-4x | Within 2% of FP16 | General use (recommended) |

### Quick Start

1. Check KV cache compression status:
   ```bash
   just kv-status
   ```

2. Enable compression with auto profile (recommended):
   ```bash
   just kv-enable auto 3
   ```

3. Start server with compression:
   ```bash
   just server-start
   ```

4. Verify compression is active:
   ```bash
   curl http://localhost:8080/health | jq '.kv_cache_compression'
   ```

For detailed documentation, see [Operations Guide - KV Cache Compression](OPERATIONS.md#kv-status).

## Admin GUI MVP (Spec 009)

A lightweight Flask-based web interface for server visibility and control, accessible at http://localhost:3000 after starting the GUI.

### Key Features

- **Server Status Dashboard**: Running state, active model, uptime, memory usage
- **Model Management View**: Available models, active model, quantization profiles
- **Basic Controls**: Start/stop/restart server via `just` recipes
- **Health Display**: Last health check result, endpoint responsiveness
- **Log Viewer**: Real-time server log viewing with auto-refresh

### Quick Start

1. Start the Admin GUI:
   ```bash
   just admin-gui
   ```

2. Access the web interface at http://localhost:3000

3. Use the dashboard to:
   - View server status and health
   - Switch between available model profiles
   - Start/stop the server with one click
   - Monitor logs in real-time

### Architecture

The GUI follows the project's governance rules by living in a separate `gui/` directory and calling `just` commands via a backend services layer:

- `gui/app.py` - Flask application entry point
- `gui/services/server_control.py` - Server start/stop/status via `just` recipes
- `gui/services/models.py` - Model profile management
- `gui/services/status_monitor.py` - Health and status monitoring
- `gui/services/log_reader.py` - Server log reading
- `gui/templates/` - Jinja2 HTML templates
- `gui/static/` - CSS and JavaScript assets

For detailed documentation, see:
- [Admin GUI Specification](specs/009-admin-gui-mvp/spec.md)
- [Admin GUI Plan](specs/009-admin-gui-mvp/plan.md)
- [HTTP Endpoints Contract](specs/009-admin-gui-mvp/contracts/http-endpoints.md)
- [Just Command Interface Contract](specs/009-admin-gui-mvp/contracts/just-command-interface.md)

## Startup Preflight & Degraded Mode (Spec 010)

Automated preflight checks before server startup with degraded mode fallback for non-critical failures.

### Key Features

- **Preflight Checks**: Memory budget, wired memory limit, disk space, and dependency integrity
- **Degraded Mode**: Automatic fallback with reduced capabilities when non-critical checks fail
- **Just Recipes**: Easy-to-use commands for preflight validation:
  - `just preflight [MODEL_PATH]` - Run preflight checks (may query model registry)
  - `just preflight-offline [MODEL_PATH]` - Run offline preflight checks (no network calls)
  - `just preflight-status [MODEL_PATH]` - Show human-readable preflight status
- **Health Endpoint**: Preflight status available via `/health` endpoint
- **Admin GUI**: Degraded mode warning banner with disabled features and fallback config

### Quick Start

1. Run preflight checks for your model:
   ```bash
   just preflight /path/to/model
   ```

2. Run offline preflight checks (no network):
   ```bash
   just preflight-offline /path/to/model
   ```

3. Start server with preflight validation:
   ```bash
   just server-start
   ```
   - Critical failures will block startup with remediation messages
   - Non-critical failures trigger degraded mode with reduced capabilities

4. Check preflight status:
   ```bash
   just preflight-status /path/to/model
   ```

### Degraded Mode Behavior

When non-critical preflight checks fail (e.g., missing TurboQuant), the system enters degraded mode:
- **Disabled Features**: TurboQuant, KV cache compression, advanced profiling
- **Fallback Quantization**: 4bit-standard (configurable in `scripts/wrapper-config/preflight-config.yaml`)
- **Fallback Profile**: 120b-balanced (safe default for 120B+ models)

For detailed documentation, see:
- [Startup Preflight Specification](specs/010-offline-002-startup/spec.md)
- [Startup Preflight Plan](specs/010-offline-002-startup/plan.md)
- [Preflight Interface Contract](specs/010-offline-002-startup/contracts/preflight-interface.md)

## Quick Start

```bash
# Initialize environment
just init

# Start server with lifecycle management (PID file, port conflict detection)
just server-start

# Check server status (process, health, uptime)
just server-status

# Stop server with graceful shutdown
just server-stop

# Or use MLX wrapper with profiles
just mlx-start --profile 120b-balanced

# Check server health
just mlx-health

# Check server status
just mlx-status

# Stop the server
just mlx-stop

# Start Admin GUI (http://localhost:3000)
just admin-gui
```

### Server Lifecycle Management

The server lifecycle management provides reliable PID file tracking, port conflict detection, and graceful shutdown capabilities through `just` recipes:

| Recipe | Description |
|---------|-------------|
| `just server-start` | Start server with PID management and port conflict detection |
| `just server-stop` | Stop server with graceful shutdown (SIGTERM -> wait -> SIGKILL) |
| `just server-status` | Check server status (process, health endpoint, uptime) |
| `just server-config` | Display current server lifecycle configuration |

For detailed documentation, see:
- [Server Lifecycle Operations](OPERATIONS.md#server-start)
- [Server Lifecycle Specification](specs/005-server-lifecycle-management/spec.md)
- [Server Lifecycle Plan](specs/005-server-lifecycle-management/plan.md)

### Model Management

The model management system provides `just` recipes for listing, selecting, and validating model profiles for 120B+ model serving on Apple Silicon:

| Recipe | Description |
|---------|-------------|
| `just models-list` | List all available model profiles with metadata |
| `just model-use <profile>` | Activate a model profile for serving (with validation) |
| `just model-status` | Show currently active model profile |

Model profiles are configured in `scripts/wrapper-config/profiles.yaml` and include quantization settings, KV cache compression, and memory estimates for Apple Silicon systems.

Example workflow:
```bash
# List available model profiles
just models-list

# Activate a model profile (with validation)
just model-use nemotron-120b

# Check current active profile
just model-status

# Start server with active profile
just mlx-start
```

For detailed documentation, see:
- [Model Management Operations](OPERATIONS.md#models-list)
- [Model Management Specification](specs/006-model-management/spec.md)
- [Model Management Plan](specs/006-model-management/plan.md)

### CLI Commands

The wrapper provides the following subcommands:

| Command | Description |
|---------|-------------|
| `start` | Start MLX server with specified profile and optional preset |
| `stop` | Stop running MLX server (graceful with --force option) |
| `status` | Check server running status and model information |
| `health` | Check server health endpoint with detailed status |
| `list-profiles` | List available model profiles from configuration |
| `list-presets` | List available startup presets for different memory tiers |

### Model Profiles

Model profiles define model paths, quantization settings, and inference arguments. Profiles are stored in `scripts/wrapper-config/profiles.yaml`.

Example profile selection:

```bash
# Use a specific profile
just mlx-start --profile 120b-balanced

# Override port and host
just mlx-start --profile 120b-balanced --port 8080 --host 127.0.0.1
```

### Startup Presets

Presets provide memory-optimized configurations for different model sizes and memory tiers. Presets are stored in `scripts/wrapper-config/presets.yaml`.

```bash
# Use a preset for 120B+ models
just mlx-start --profile 120b-extreme --preset 120b-extreme
```

### Configuration Files

- **profiles.yaml**: Model profile definitions with quantization and inference settings
- **presets.yaml**: Startup presets targeting specific memory tiers and model sizes

See [`scripts/wrapper-config/profiles.yaml`](scripts/wrapper-config/profiles.yaml) and [`scripts/wrapper-config/presets.yaml`](scripts/wrapper-config/presets.yaml) for examples.

### Documentation

- [Wrapper Operations](OPERATIONS.md#mlx-wrapper-operations) - Detailed operational procedures
- [CLI Interface Contract](specs/004-mlx-server-wrapper/contracts/cli-interface.md) - Full CLI specification
- [Health Endpoint Contract](specs/004-mlx-server-wrapper/contracts/health-endpoint.md) - Health check API specification
- [Quickstart Guide](specs/004-mlx-server-wrapper/quickstart.md) - Step-by-step getting started guide


## Security Configuration

The Local MLX Server includes security hardening options for local inference infrastructure. Key security features:

### Network Security
- **Default localhost-only**: Server binds to `127.0.0.1` by default
- **Network binding control**: Use `ALLOW_NETWORK_BINDING` environment variable (default: `false`)
- **Warning**: Only enable network binding with additional security measures in place

### Model Path Security
- **Authorized directories**: Restrict model loading to `AUTHORIZED_MODEL_DIRS`
- **Path traversal protection**: Rejects `../` and `..\\` patterns
- **Fail-closed**: Invalid paths return 403 Forbidden

### Environment Variable Protection
- **Sensitive data redaction**: Enable `REDACT_SENSITIVE_VARS=true` to prevent exposure in logs
- **File permissions**: Set `.env` file to mode 600 (`chmod 600 .env`)

### Endpoint Hardening
- **Disable non-essential endpoints**: Use `DISABLE_HEALTH_ENDPOINT`, `DISABLE_METRICS_ENDPOINT`, `DISABLE_MODELS_ENDPOINT`
- **Input validation**: JSON schema validation, prompt length limits (4096 chars), content-type enforcement

### Security Validation

Run the security check recipe:

```bash
just security-check
```

For detailed security documentation, see:
- [Operations Guide - Security Section](OPERATIONS.md#security-operations)
- [Security Validation Guide](docs/security-validation.md)
- [API Endpoint Contracts](specs/002-security-implementation/contracts/api-endpoints.md)

## Scope and Non-Goals

**In scope**:

- Reproducible local server startup and operational scripts.
- MLX and TurboQuant integration updates.
- Inference arguments tuning for memory, latency, and quality tradeoffs.
- Stable OpenAI-compatible local API behavior.

**Out of scope**:

- Building full-stack web products in this directory.
- App UI frameworks and product-level backend features.
- Data platform expansion unrelated to inference serving.

## Related Documentation

- [Operations Guide](OPERATIONS.md) - Detailed operational procedures and `just` command reference
- [Agent Rules](AGENTS.md) - Operational charter for AI agents working in this repository
- [Governance](GOVERNANCE.md) - Project constitution, standards, and governance policies
- [Contributing](CONTRIBUTING.md) - Guidelines for contributors
