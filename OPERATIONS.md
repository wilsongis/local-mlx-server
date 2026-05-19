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
