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
