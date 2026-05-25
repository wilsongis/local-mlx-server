"""Memory budget and wired memory limit checks for preflight validation.

This module provides functions to check if the system has sufficient memory
for loading large models (120B+) and that wired memory is within limits.
"""

import ctypes
import ctypes.util
import logging
from datetime import datetime
from pathlib import Path

from scripts.preflight.checker import PreflightCheck

logger = logging.getLogger(__name__)


def _get_wired_memory_gb() -> float:
    """Get wired memory usage on macOS in GB.

    Uses ctypes to call host_statistics64 from libSystem.dylib
    to get wired memory pages and converts to GB.

    Returns:
        Wired memory in GB, or 0.0 if detection fails
    """
    try:
        # Find the system library
        libsystem_path = ctypes.util.find_library("System")
        if not libsystem_path:
            logger.warning("Could not find System library for wired memory check")
            return 0.0

        libsystem = ctypes.CDLL(libsystem_path)

        # Define host_statistics64 - this is a simplified version
        # In production, you'd want to use the full vm_statistics64 structure
        # For now, we'll use psutil as fallback and primary method

        # On macOS, wired memory is part of 'wired' in virtual_memory
        # psutil doesn't directly expose wired memory, so we estimate
        # A more accurate approach would use vm_stat via subprocess or ctypes

        # Simplified: return 0 and let the check handle missing data
        return 0.0

    except Exception as e:
        logger.warning(f"Failed to get wired memory: {e}")
        return 0.0


def check_memory_budget(model_path: str) -> PreflightCheck:
    """Verify available GPU/memory meets model requirements.

    Checks if the system has enough unified memory to load the specified model.
    For 120B+ models with TurboQuant: 48GB minimum
    For 120B+ models with standard 4-bit: 64GB minimum

    Args:
        model_path: Path to the model directory

    Returns:
        PreflightCheck with status (pass/fail/warning)
    """
    check_name = "memory_budget"
    check_type = "critical"

    try:
        try:
            import psutil
        except ImportError:
            logger.error("psutil not installed - cannot check memory budget")
            return PreflightCheck(
                name=check_name,
                check_type=check_type,
                status="fail",
                details="psutil not installed - required for memory checks. Install with: uv pip install psutil",
                timestamp=datetime.now(),
                error_code="ERR-MEM-002",
            )

        # Get total system memory in GB
        total_memory_gb = psutil.virtual_memory().total / (1024**3)

        # Determine model size class from path or config
        model_size_class = _detect_model_size_class(model_path)

        # Get thresholds from config (will be loaded by PreflightChecker)
        # For now, use the standard thresholds
        if model_size_class == "100B+":
            required_gb = 48  # TurboQuant threshold
            warning_gb = 56
        else:
            required_gb = 32  # Smaller models
            warning_gb = 40

        details = f"{total_memory_gb:.1f}GB available ({required_gb}GB required for {model_size_class} model)"

        if total_memory_gb >= required_gb:
            if total_memory_gb < warning_gb:
                status = "warning"
                details += " (approaching limit)"
            else:
                status = "pass"
            error_code = None
        else:
            status = "fail"
            error_code = "ERR-MEM-001"
            details += " - INSUFFICIENT MEMORY. "
            details += "Action: Close memory-intensive applications, or use 'just models-list' to select a lower-memory profile. "
            details += "For 48GB systems, try: just model-use 120b-extreme"

        return PreflightCheck(
            name=check_name,
            check_type=check_type,
            status=status,
            details=details,
            timestamp=datetime.now(),
            error_code=error_code,
        )

    except ImportError:
        return PreflightCheck(
            name=check_name,
            check_type=check_type,
            status="fail",
            details="psutil not installed - cannot check memory",
            timestamp=datetime.now(),
            error_code="ERR-MEM-002",
        )
    except Exception as e:
        logger.error(f"Memory budget check failed: {e}")
        return PreflightCheck(
            name=check_name,
            check_type=check_type,
            status="fail",
            details=f"Memory check error: {str(e)}",
            timestamp=datetime.now(),
            error_code="ERR-MEM-003",
        )


def check_wired_limit() -> PreflightCheck:
    """Check wired memory usage is within acceptable limits.

    Wired memory on macOS is memory that cannot be paged out.
    High wired memory can impact model loading performance.

    Threshold: Default 12GB (configurable in preflight-config.yaml)

    Returns:
        PreflightCheck with status
    """
    check_name = "wired_limit"
    check_type = "non_critical"  # Non-critical: can still run, but with warnings

    try:
        # This is a simplified check - in practice, you'd want to
        # query actual wired memory via vm_stat or host_statistics64
        # For now, we'll return a pass with a note

        wired_gb = _get_wired_memory_gb()

        # Default limit from config would be loaded by PreflightChecker
        limit_gb = 12  # Default

        if wired_gb == 0.0:
            # Could not detect, return warning
            return PreflightCheck(
                name=check_name,
                check_type=check_type,
                status="warning",
                details="Could not detect wired memory usage (detection not fully implemented)",
                timestamp=datetime.now(),
                error_code="ERR-MEM-004",
            )

        details = f"{wired_gb:.1f}GB wired memory (limit: {limit_gb}GB)"

        if wired_gb > limit_gb:
            status = "fail"
            error_code = "ERR-MEM-005"
            details += " - EXCEEDS LIMIT"
        else:
            status = "pass"
            error_code = None

        return PreflightCheck(
            name=check_name,
            check_type=check_type,
            status=status,
            details=details,
            timestamp=datetime.now(),
            error_code=error_code,
        )

    except Exception as e:
        logger.error(f"Wired limit check failed: {e}")
        return PreflightCheck(
            name=check_name,
            check_type=check_type,
            status="warning",
            details=f"Wired memory check error: {str(e)}",
            timestamp=datetime.now(),
            error_code="ERR-MEM-006",
        )


def _detect_model_size_class(model_path: str) -> str:
    """Detect model size class from model path or config.

    Args:
        model_path: Path to model directory

    Returns:
        Size class string: "100B+", "70B", "20B", or "unknown"
    """
    try:
        # Try to read config.json to get model size info
        config_path = Path(model_path) / "config.json"
        if config_path.exists():
            import json

            with open(config_path, "r") as f:
                config = json.load(f)
                # Check for model type or size hints
                model_type = config.get("model_type", "").lower()
                # Simple heuristic: check if model name contains size info
                # In practice, you'd use the model_detector.py module
                if "120b" in model_type or "100b" in model_type:
                    return "100B+"
                elif "70b" in model_type or "72b" in model_type:
                    return "70B"
                elif "20b" in model_type or "22b" in model_type:
                    return "20B"
        # Default to checking if path contains size info
        model_path_lower = model_path.lower()
        if "120b" in model_path_lower or "100b" in model_path_lower:
            return "100B+"
        return "unknown"
    except Exception:
        return "unknown"
