"""
Server control service - interfaces with `just` commands for server start/stop.

Implements the just command interface contract from contracts/just-command-interface.md
"""

import subprocess
from pathlib import Path
from typing import Tuple

# Project root is the parent of the gui/ directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def run_just_command(command: str, timeout: int = 30) -> Tuple[bool, str, str]:
    """
    Execute a just command and return the result.

    Args:
        command: The just command to run (e.g., "start", "stop")
        timeout: Maximum seconds to wait for command completion

    Returns:
        tuple: (success: bool, stdout: str, stderr: str)
    """
    try:
        result = subprocess.run(
            ["just", command],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(PROJECT_ROOT),
        )
        success = result.returncode == 0
        output = result.stdout.strip() if result.stdout else ""
        error = result.stderr.strip() if result.stderr else ""

        # Prefer stdout for success message, stderr for error
        message = error if (not success and error) else output

        # Handle edge case: server started outside GUI
        if command == "start" and not success:
            # Check if server might already be running
            import requests

            try:
                r = requests.get("http://localhost:8000/health", timeout=2)
                if r.status_code == 200:
                    return (True, "Server is already running (started outside GUI)", "")
            except Exception:
                pass

        return (success, message, error)

    except subprocess.TimeoutExpired:
        # Timeout might mean server is starting (long startup for large models)
        if command == "start":
            return (
                True,
                f"Command timed out after {timeout} seconds - server may still be starting",
                "",
            )
        return (False, "", f"Command timed out after {timeout} seconds")
    except FileNotFoundError:
        return (False, "", "just command not found. Install with: brew install just")
    except Exception as e:
        return (False, "", str(e))
