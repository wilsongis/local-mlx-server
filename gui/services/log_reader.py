"""
Log reading service - accesses server logs for display.

Implements log reading contract for the Admin GUI MVP.
"""

from pathlib import Path
from typing import List

from .models import LogEntry

# Project root is the parent of the gui/ directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def read_logs(max_lines: int = 100) -> List[LogEntry]:
    """
    Read recent server log entries.

    Attempts to read from common log locations:
    1. Server output captured by just commands
    2. Log files in project root

    Args:
        max_lines: Maximum number of log lines to return

    Returns:
        List of LogEntry objects
    """
    log_entries: List[LogEntry] = []

    # Try to get logs via just command
    try:
        import subprocess

        result = subprocess.run(
            ["just", "logs"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(PROJECT_ROOT),
        )
        if result.returncode == 0 and result.stdout:
            lines = result.stdout.strip().split("\n")
            # Take the last max_lines
            for line in lines[-max_lines:]:
                if line.strip():
                    log_entries.append(parse_log_line(line))
    except Exception:
        # If just logs fails, return empty list
        pass

    return log_entries


def parse_log_line(line: str) -> LogEntry:
    """
    Parse a single log line into a LogEntry.

    Args:
        line: Raw log line string

    Returns:
        LogEntry with parsed data
    """
    # Simple parsing - can be enhanced later
    level = "info"
    if "error" in line.lower():
        level = "error"
    elif "warn" in line.lower():
        level = "warning"
    elif "debug" in line.lower():
        level = "debug"

    return LogEntry(message=line.strip(), level=level, source="file")
