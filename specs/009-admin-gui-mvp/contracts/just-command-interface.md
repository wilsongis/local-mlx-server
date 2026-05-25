# Contract: just Command Interface

**Feature**: Admin GUI MVP (009-admin-gui-mvp)
**Date**: 2026-05-24
**Status**: Complete

---

## Overview

This contract defines how the Admin GUI interfaces with `just` commands for server control, following Principle IV (Just Command Bridge) of the constitution.

---

## Interface Specification

### Command Execution Contract

The GUI will execute `just` commands via Python's `subprocess` module.

**Function Signature**:
```python
def run_just_command(command: str, timeout: int = 30) -> tuple[bool, str, str]:
    """
    Execute a just command and return the result.
    
    Args:
        command: The just command to run (e.g., "start", "stop")
        timeout: Maximum seconds to wait for command completion
    
    Returns:
        tuple: (success: bool, stdout: str, stderr: str)
    """
```

**Implementation Contract**:
```python
import subprocess
from typing import Tuple

def run_just_command(command: str, timeout: int = 30) -> Tuple[bool, str, str]:
    """Execute a just command via subprocess."""
    try:
        result = subprocess.run(
            ["just", command],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd="/Users/wilsonm/development/local-mlx-server"  # Project root
        )
        success = (result.returncode == 0)
        output = result.stdout.strip() if result.stdout else ""
        error = result.stderr.strip() if result.stderr else ""
        
        # Prefer stdout for success message, stderr for error
        message = error if (not success and error) else output
        return (success, message, error)
    
    except subprocess.TimeoutExpired:
        return (False, "", f"Command timed out after {timeout} seconds")
    except FileNotFoundError:
        return (False, "", "just command not found. Is just installed?")
    except Exception as e:
        return (False, "", str(e))
```

---

## Supported Commands

### 1. `just start`

**Purpose**: Start the MLX server.

**Expected Behavior**:
- Starts the MLX server process (typically via `mlx_lm.server`)
- Returns success when server is successfully started
- Returns failure with error message if startup fails

**GUI Integration**:
```python
@app.route('/api/start', methods=['POST'])
def start_server():
    success, message, error = run_just_command('start')
    return jsonify({
        'success': success,
        'message': message or ('Server started successfully' if success else 'Failed to start server'),
        'timestamp': datetime.now().isoformat()
    })
```

**Error Handling**:
- If `just` command not found: Return error suggesting to install `just`
- If command times out: Return timeout error
- If server fails to start: Return error from stderr

---

### 2. `just stop`

**Purpose**: Stop the MLX server.

**Expected Behavior**:
- Stops the running MLX server process
- Returns success when server is successfully stopped
- Returns failure with error message if stop fails

**GUI Integration**:
```python
@app.route('/api/stop', methods=['POST'])
def stop_server():
    success, message, error = run_just_command('stop')
    return jsonify({
        'success': success,
        'message': message or ('Server stopped successfully' if success else 'Failed to stop server'),
        'timestamp': datetime.now().isoformat()
    })
```

---

### 3. `just status` (Optional)

**Purpose**: Get detailed server status (if available in justfile).

**Expected Behavior**:
- Returns server status information
- May include process ID, uptime, model info

**GUI Integration** (if available):
```python
def get_server_details():
    success, message, _ = run_just_command('status')
    if success:
        # Parse status output for additional details
        return parse_status_output(message)
    return None
```

---

## Contract Constraints

1. **Command Availability**: The GUI should gracefully handle missing `just` commands:
   - Check if `just` is installed before attempting commands
   - Display clear error message if command is not found in justfile

2. **Working Directory**: Commands must be executed from the project root (`/Users/wilsonm/development/local-mlx-server`) to ensure justfile is found.

3. **Timeout Handling**: All commands should have a reasonable timeout (default 30 seconds) to prevent hanging.

4. **Output Capture**: Both stdout and stderr should be captured for debugging and error reporting (FR-006).

5. **Security**: Commands are executed locally with the same permissions as the GUI process. No user input is passed directly to commands (prevents command injection).

---

## Testing Contract

```python
import pytest
from unittest.mock import patch, MagicMock

def test_run_just_command_success():
    """Test successful just command execution."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Server started\n",
            stderr=""
        )
        success, message, error = run_just_command('start')
        assert success == True
        assert "started" in message.lower()

def test_run_just_command_failure():
    """Test failed just command execution."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Port 8000 already in use\n"
        )
        success, message, error = run_just_command('start')
        assert success == False
        assert "port" in message.lower() or "port" in error.lower()

def test_run_just_command_timeout():
    """Test just command timeout."""
    with patch('subprocess.run', side_effect=subprocess.TimeoutExpired(cmd="just", timeout=30)):
        success, message, error = run_just_command('start', timeout=5)
        assert success == False
        assert "timeout" in error.lower()

def test_run_just_command_not_found():
    """Test just command not found."""
    with patch('subprocess.run', side_effect=FileNotFoundError("just not found")):
        success, message, error = run_just_command('start')
        assert success == False
        assert "not found" in error.lower() or "just" in error.lower()
```

---

## Integration with Health Polling

The `just` command interface works in conjunction with the health endpoint polling:

1. User clicks "Start Server" → `POST /api/start` → `just start`
2. GUI polls `GET /api/status` → polls `http://localhost:8000/health`
3. When health check succeeds → status changes to "running"
4. User clicks "Stop Server" → `POST /api/stop` → `just stop`

This dual approach ensures:
- Commands are used for control (Principle IV)
- Health endpoint is used for authoritative status (handles server started outside GUI)

---

## References

- Constitution Principle IV: Just Command Bridge
- Feature Spec: [specs/009-admin-gui-mvp/spec.md](specs/009-admin-gui-mvp/spec.md) (FR-002, FR-004, FR-006)
- Research: [specs/009-admin-gui-mvp/research.md](specs/009-admin-gui-mvp/research.md) (Decision 3)
- HTTP Endpoints Contract: [contracts/http-endpoints.md](contracts/http-endpoints.md)
