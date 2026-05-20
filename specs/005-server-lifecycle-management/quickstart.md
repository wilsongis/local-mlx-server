# Server Lifecycle Management Quickstart

## Overview

The server lifecycle management feature provides reliable PID file tracking, port conflict detection, and graceful shutdown capabilities for the Local MLX Server.

## Quick Reference

### Start Server

```bash
# Start with default settings
just server-start

# Start with custom model path
MODEL_PATH=/path/to/model just server-start

# Start with custom port
PORT=8080 just server-start
```

### Check Status

```bash
# Check server status
just server-status

# Example output
Server Status: HEALTHY
  PID: 12345
  Uptime: 5 minutes
  Port: 8080
  Health: healthy
```

### Stop Server

```bash
# Graceful stop (SIGTERM -> wait -> SIGKILL)
just server-stop

# Stop with custom timeout
SERVER_GRACEFUL_TIMEOUT=60 just server-stop
```

### Configuration

```bash
# Display current configuration
just server-config

# Output example
Server Lifecycle Configuration:
  PID File: /tmp/mlx-server.pid
  Graceful Timeout: 30s
  Log Level: INFO
  Model Path: ./models
  Host: 127.0.0.1
  Port: 8000
```

## Key Features

### PID File Management
- Atomic PID file writes with `fcntl.flock` to prevent corruption
- Automatic stale PID detection and cleanup
- Prevents duplicate server starts

### Port Conflict Detection
- Detects ports in use before server start
- Configurable port scan range (default: 10 ports)
- Auto-assigns available port if conflict detected

### Graceful Shutdown
- Sends SIGTERM for graceful shutdown
- Waits for configurable timeout (default: 30s)
- Sends SIGKILL if process doesn't stop gracefully
- Cleans up PID file after shutdown

### Health Monitoring
- Queries `/health` endpoint for server health
- Reports status: healthy, degraded, stopped, stale_pid
- Shows uptime and process information

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVER_PID_FILE` | `/tmp/mlx-server.pid` | Path to PID file |
| `SERVER_GRACEFUL_TIMEOUT` | `30` | Graceful shutdown timeout (seconds) |
| `SERVER_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `MODEL_PATH` | `./models` | Path to model directory |
| `HOST` | `127.0.0.1` | Host to bind to |
| `PORT` | `8000` | Port to listen on |

## Performance Requirements

- **NFR-001**: Server start <5s (excluding model load)
- **NFR-002**: Status check <2s
- **NFR-005**: Port scan <1s

## Troubleshooting

### Server Won't Start (Already Running)
```bash
# Check if server is running
just server-status

# If stale PID file exists, it will be auto-cleaned on next start
# Or manually remove: rm /tmp/mlx-server.pid
```

### Port Conflict
```bash
# Check what's using the port
lsof -i :8080

# Use a different port
PORT=8081 just server-start
```

### Server Won't Stop
```bash
# Try graceful stop first
just server-stop

# If unresponsive, increase timeout
SERVER_GRACEFUL_TIMEOUT=60 just server-stop
```

## Next Steps

- [Full Operations Guide](OPERATIONS.md#server-start)
- [Server Lifecycle Specification](spec.md)
- [Implementation Plan](plan.md)
- [Task List](tasks.md)
