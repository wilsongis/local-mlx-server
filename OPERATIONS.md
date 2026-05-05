# Operations Guide

## Overview

This guide covers all operational aspects of running the Local MLX Server, including server lifecycle management, model operations, and troubleshooting procedures.

## Just Command Reference

The `just` command bridge is the primary control interface for all operational workflows. Using `just` recipes ensures reproducibility across machines and sessions.

### Core Commands

| Command | Description |
|---------|-------------|
| `just start` | Start the server in a containerized environment |
| `just run` | Start the server natively (non-containerized) |
| `just stop` | Stop the running server |
| `just status` | Check server health and status |
| `just lint` | Run code linting (RUFF) |
| `just test` | Run test suite |
| `just security-check` | Validate security configuration |

### Planned Commands (Coming Soon)

| Command | Description |
|---------|-------------|
| `just server-start` | Explicit server startup |
| `just server-stop` | Explicit server shutdown |
| `just server-status` | Detailed server status report |
| `just models-list` | List available model profiles |
| `just model-use <profile>` | Switch to a specific model profile |

## Server Startup

### Native Start (Recommended for Development)

```bash
# Ensure dependencies are installed via uv
uv sync

# Start the server with default settings
just run
```

### Containerized Start (Production-like)

```bash
# Start using Containerfile
just start
```

### Server Configuration

The server uses `mlx_lm.server` as the OpenAI-compatible endpoint. Key configuration areas:

- **Model Path**: Point to your quantized model directory
- **Context Length**: Adjust based on memory constraints
- **Quantization Settings**: Per-path hybrid quantization parameters
- **KV Cache**: Compression settings for long context support

## Server Lifecycle Management

### Health Checks

```bash
# Check if server is responding
just status

# Manual health check
curl http://localhost:8000/health
```

### Stopping the Server

```bash
# Using just command
just stop

# Manual process termination (if needed)
pkill -f "mlx_lm.server"
```

## Model Management

### Listing Available Models

```bash
just models-list
```

### Switching Model Profiles

```bash
# Use a specific model profile
just model-use nemotron-120b-q2

# View current active profile
just model-use
```

## Security Operations

### Security Configuration

The Local MLX Server includes security hardening options configured via environment variables in `.env` (see `.env.example` for reference).

#### Network Security

By default, the server binds to `127.0.0.1` (localhost only) to prevent network access:

```bash
# .env - Localhost only (default, secure)
MLX_SERVER_HOST="127.0.0.1"
ALLOW_NETWORK_BINDING=false

# .env - Allow network binding (use with caution)
ALLOW_NETWORK_BINDING=true
MLX_SERVER_HOST="0.0.0.0"  # Binds to all interfaces
```

**Warning**: Enabling network binding exposes the server beyond localhost. Ensure additional network security measures are in place.

#### Model Path Security

Restrict model loading to authorized directories:

```bash
# .env - Colon-separated list of authorized directories
AUTHORIZED_MODEL_DIRS="./models:/path/to/other/authorized/models"
```

The server validates that all model paths resolve within authorized directories. Path traversal attempts (e.g., `../`) are rejected.

#### Environment Variable Protection

Prevent sensitive data exposure in logs and error messages:

```bash
# .env - Enable redaction of sensitive variables
REDACT_SENSITIVE_VARS=true
```

Sensitive patterns include: `*_KEY`, `*_TOKEN`, `*_SECRET`, `*_PASSWORD`, `*_CREDENTIAL*`, `MLX_MODEL_PATH`, `AUTHORIZED_MODEL_DIRS`.

#### Endpoint Hardening

Disable non-essential endpoints for production deployments:

```bash
# .env - Disable specific endpoints
DISABLE_HEALTH_ENDPOINT=true
DISABLE_METRICS_ENDPOINT=true
DISABLE_MODELS_ENDPOINT=true
```

### Security Validation

Use the `just` recipe to validate security configuration:

```bash
# Run security check
just security-check
```

Expected output:
```
Running security configuration check...
Checking .env.example...
Security check passed.
```

The `security-check` recipe verifies:
- `ALLOW_NETWORK_BINDING=false` in `.env.example`
- `MLX_SERVER_HOST="127.0.0.1"` in `.env.example`
- `REDACT_SENSITIVE_VARS=true` is set
- `AUTHORIZED_MODEL_DIRS` is configured
- `.env` file permissions (should be 600)

### API Endpoint Security

#### Input Validation

All API inputs are validated for:
- JSON schema compliance
- Prompt length limits (max 4096 characters)
- Rejection of shell metacharacters and path traversal sequences (`../`, `..\\`)
- Content-type validation (`application/json` required)

#### Authentication

The server is designed for localhost-only operation by default. For network-accessible deployments:
- Use reverse proxy with authentication (nginx, Caddy)
- Consider API gateway with rate limiting
- Implement mTLS for service-to-service communication

#### Rate Limiting

For production deployments, implement rate limiting at the reverse proxy level:

```nginx
# nginx example
location /v1/ {
    limit_req zone=mlx_server burst=10 nodelay;
    proxy_pass http://127.0.0.1:8000;
}
```

### Path Validation

Model paths are validated using:
1. **Resolution**: Convert to absolute path with symlink resolution
2. **Prefix matching**: Ensure path starts with authorized directory
3. **Traversal detection**: Reject paths containing `../` or `..\\`
4. **Fail-closed**: Invalid paths return 403 Forbidden

### Environment File Security

Secure your `.env` file:

```bash
# Set restrictive permissions (macOS/Linux)
chmod 600 .env

# Verify permissions
ls -la .env
# Should show: -rw------- (600)
```

**Warning**: Never commit `.env` to version control. It's already in `.gitignore`.

### Security Documentation

For detailed security validation patterns and helper functions, see:
- [Security Validation Guide](docs/security-validation.md)
- [API Endpoint Contracts](specs/002-security-implementation/contracts/api-endpoints.md)
- [Security Quickstart](specs/002-security-implementation/quickstart.md)

## Troubleshooting

### Common Issues

#### Server Fails to Start

**Symptoms**: Server exits immediately or fails to bind to port

**Checks**:
1. Verify port 8000 is not in use: `lsof -i :8000`
2. Check model path exists and is accessible
3. Verify memory availability: `memory_pressure` (macOS)
4. Review server logs for specific errors

#### Out of Memory Errors

**Symptoms**: Server crashes with memory-related errors during model load

**Solutions**:
1. Use more aggressive quantization (lower expert bit-width)
2. Reduce context length
3. Enable KV cache compression
4. Close other memory-intensive applications

#### Poor Inference Performance

**Symptoms**: Slow token generation or high latency

**Optimizations**:
1. Verify MLX is using Metal (GPU) acceleration
2. Check quantization settings balance (attention vs expert paths)
3. Monitor KV cache memory usage at long contexts
4. Consider per-path hybrid quantization tuning

### Debug Mode

For detailed debugging information:

```bash
# Run with verbose output
just run --verbose

# Check MLX logs
tail -f ~/.cache/mlx/logs/server.log
```

## Operational Direction

Near-term operational priorities:

- Keep model serving minimal and deterministic.
- Preserve compatibility with large-model local execution constraints.
- Optimize defaults for long-context, memory-constrained Apple Silicon usage.
- Track MLX and TurboQuant changes that impact stability, speed, and compression behavior.
- Standardize all operator workflows behind `just` recipes before adding any separate control UI.

## Related Documentation

- [README](README.md) - Project overview and navigation index
- [Agent Rules](AGENTS.md) - Operational charter and agent guidelines
- [Governance](GOVERNANCE.md) - Project constitution and standards
- [Contributing](CONTRIBUTING.md) - Development workflow and testing guidelines
