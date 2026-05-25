"""Disk space check for preflight validation.

This module provides functions to verify sufficient disk space
for model loading and operation.
"""

import logging
from datetime import datetime

from scripts.preflight.checker import PreflightCheck

logger = logging.getLogger(__name__)


def check_disk_space(path: str = ".") -> PreflightCheck:
    """Verify sufficient disk space for model loading and operation.

    Checks if the specified path has at least the minimum required disk space.
    Accounts for model size + swap + temporary files.

    Args:
        path: Path to check (default: current directory)

    Returns:
        PreflightCheck with status (pass/fail/warning)

    Threshold:
        - Minimum: 50GB (configurable in preflight-config.yaml)
        - Accounts for model size + swap + temporary files
    """
    check_name = "disk_space"
    check_type = "critical"

    try:
        try:
            import shutil
        except ImportError:
            logger.error("shutil not available - cannot check disk space")
            return PreflightCheck(
                name=check_name,
                check_type=check_type,
                status="fail",
                details="shutil module not available - required for disk checks",
                timestamp=datetime.now(),
                error_code="ERR-DISK-003",
            )

        # Get disk usage statistics
        total, used, free = shutil.disk_usage(path)

        # Convert to GB
        total_gb = total / (1024**3)
        free_gb = free / (1024**3)

        # Default minimum required (will be overridden by config in PreflightChecker)
        min_required_gb = 50

        details = f"{free_gb:.1f}GB free of {total_gb:.1f}GB total (min required: {min_required_gb}GB)"

        if free_gb >= min_required_gb:
            if free_gb < min_required_gb * 1.2:  # Less than 120% of minimum
                status = "warning"
                details += " (approaching limit)"
            else:
                status = "pass"
            error_code = None
        else:
            status = "fail"
            error_code = "ERR-DISK-001"
            details += " - INSUFFICIENT DISK SPACE"

        return PreflightCheck(
            name=check_name,
            check_type=check_type,
            status=status,
            details=details,
            timestamp=datetime.now(),
            error_code=error_code,
        )

    except Exception as e:
        logger.error(f"Disk space check failed: {e}")
        return PreflightCheck(
            name=check_name,
            check_type=check_type,
            status="fail",
            details=f"Disk space check error: {str(e)}",
            timestamp=datetime.now(),
            error_code="ERR-DISK-002",
        )
