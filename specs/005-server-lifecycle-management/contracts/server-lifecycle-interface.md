# ServerLifecycleManager Class Interface

## Overview

This document defines the interface contract for the `ServerLifecycleManager` class in `scripts/server-lifecycle.py`.

## Class: ServerLifecycleManager

### Constructor

```python
ServerLifecycleManager(
    pid_file: str = "/tmp/mlx-server.pid",
    log_level: str = "INFO",
    graceful_timeout: int = 30
)
```

**Parameters**:
- `pid_file`: Path to PID file for process tracking
- `log_level`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `graceful_timeout`: Seconds to wait for graceful shutdown before SIGKILL

### Methods

#### PID File Management

##### create_pid_file(pid: int) -> bool
Atomically create PID file with file locking to prevent corruption.

**Returns**: True if successful, False otherwise

##### read_pid_file() -> Optional[int]
Read and validate PID from PID file.

**Returns**: PID as integer if valid, None otherwise

##### remove_pid_file() -> bool
Remove PID file if it exists.

**Returns**: True if successful, False otherwise

##### validate_pid_file() -> tuple[Optional[int], bool]
Validate PID file: read PID, check if process is alive.

**Returns**: Tuple of (pid, is_valid) where:
- `pid`: PID from file, or None if invalid
- `is_valid`: True if PID file exists and process is running

##### cleanup_stale_pid() -> bool
Remove stale PID file if process is not running.

**Returns**: True if successful or no stale PID found, False on error

#### Process Validation

##### is_process_alive(pid: int) -> bool
Check if a process with given PID is alive using psutil.

**Returns**: True if process is running and not zombie, False otherwise

#### Port Conflict Detection

##### is_port_in_use(port: int, host: str = "127.0.0.1") -> tuple[bool, Optional[int]]
Check if port is in use. Uses psutil for cross-platform port detection.

**Returns**: Tuple of (in_use, conflicting_pid) where:
- `in_use`: True if port is in use and listening
- `conflicting_pid`: PID of process using the port, or None

##### find_available_port(start_port: int = 8080, scan_depth: int = 10) -> Optional[int]
Find next available port in range.

**Returns**: Available port number, or None if no port found

#### Health Endpoint Checker

##### check_health(port: int = 8080, host: str = "127.0.0.1", timeout: int = 5) -> dict[str, Any]
Query /health endpoint and return status dict.

**Returns**: Dictionary with keys:
- `healthy`: Boolean indicating if server is healthy
- `status`: String status ("healthy", "http_XXX", "unreachable")
- `response`: Response JSON if healthy, None or error string otherwise

#### Server Lifecycle Operations

##### start_server(model_path: str, port: int = 8080, host: str = "127.0.0.1", extra_args: Optional[list] = None) -> bool
Start MLX server with PID management.

**Behavior**:
1. Check for existing PID file
2. Clean up stale PID if present
3. Check port conflict
4. Build and execute mlx_lm.server command
5. Create PID file after successful start

**Returns**: True if server started successfully, False otherwise

##### stop_server() -> bool
Stop server with graceful shutdown (SIGTERM, wait, SIGKILL).

**Behavior**:
1. Read and validate PID file
2. Send SIGTERM for graceful shutdown
3. Wait for graceful timeout period
4. Poll process status and health endpoint
5. Send SIGKILL if timeout exceeded
6. Remove PID file after process exits

**Returns**: True if server stopped successfully, False otherwise

##### get_status(port: int = 8080, host: str = "127.0.0.1") -> dict[str, Any]
Get comprehensive server status.

**Returns**: Dictionary with keys:
- `running`: Boolean indicating if server is running
- `pid`: Process ID if running, None otherwise
- `uptime`: Uptime in seconds if running, None otherwise
- `port`: Server port
- `health`: Health check result dict, or None
- `status`: String status ("healthy", "degraded", "stopped", "stale_pid", "zombie")

##### format_status(status: dict[str, Any]) -> str
Format status dict into human-readable output.

**Returns**: Formatted string with server status information

## CLI Entry Points

The script supports three subcommands via argparse:

### start
```bash
python scripts/server-lifecycle.py start --pid-file PATH --port PORT --host HOST --model PATH --log-level LEVEL --graceful-timeout SECONDS
```

**Required**: `--model`
**Optional**: `--pid-file`, `--port`, `--host`, `--log-level`, `--graceful-timeout`

### stop
```bash
python scripts/server-lifecycle.py stop --pid-file PATH --graceful-timeout SECONDS
```

**Optional**: `--pid-file`, `--graceful-timeout`

### status
```bash
python scripts/server-lifecycle.py status --pid-file PATH --port PORT --host HOST [--json]
```

**Optional**: `--pid-file`, `--port`, `--host`, `--json`

## Performance Requirements

| Requirement | Target | Test |
|--------------|--------|------|
| Server start (excluding model load) | <5s | T034.1 / TestPerformanceStart |
| Status check | <2s | T034.2 / TestPerformanceStatus |
| Port scan (10 ports) | <1s | T034.3 / TestPerformancePortScan |

## Error Handling

- All methods return boolean success/failure or None for optional values
- Logging is used for all lifecycle events (configurable via log_level)
- Exceptions are caught and logged, not propagated to caller
- File operations use try/except to handle permission and IO errors

## Dependencies

- **psutil**: Process management, port conflict detection
- **requests**: Health endpoint checking
- **fcntl**: File locking for atomic PID file operations

## Thread Safety

- PID file operations use `fcntl.flock` for atomic access
- No global state; each `ServerLifecycleManager` instance is independent
- Not designed for concurrent access to same PID file (use file locking)

## Future Enhancements

- Multi-instance configuration via `scripts/wrapper-config/instances.yaml`
- True request draining (requires mlx_lm.server wrapper integration)
- Instance-specific start/stop/status commands
