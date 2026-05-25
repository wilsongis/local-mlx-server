"""Dependency integrity checks for preflight validation.

This module provides functions to verify that required dependencies
are installed and compatible.
"""

import logging
from datetime import datetime

from scripts.preflight.checker import PreflightCheck

logger = logging.getLogger(__name__)


def check_dependencies() -> PreflightCheck:
    """Check all dependency integrity.

    Verifies:
    - mlx-lm is importable
    - Version >= 0.19.0 (minimum for TurboQuant)
    - mlx core dependency satisfied
    - psutil is available (for memory checks)

    Returns:
        PreflightCheck with version info and status
    """
    check_name = "dependencies"
    check_type = "critical"

    details_parts = []
    failed_deps = []

    # Check mlx-lm
    mlx_status, mlx_details = _check_mlx_integrity()
    details_parts.append(mlx_details)
    if mlx_status == "fail":
        failed_deps.append("mlx-lm")

    # Check psutil (needed for memory checks)
    psutil_status, psutil_details = _check_psutil_available()
    details_parts.append(psutil_details)
    if psutil_status == "fail":
        failed_deps.append("psutil")

    # Check TurboQuant (non-critical, but useful to know)
    turbo_status, turbo_details = _check_turboquant_available()
    details_parts.append(turbo_details)

    # Check KV cache support (non-critical)
    kv_status, kv_details = _check_kv_cache_support()
    details_parts.append(kv_details)

    # Determine overall status
    if failed_deps:
        status = "fail"
        error_code = "ERR-DEP-001"
        details = f"Missing dependencies: {', '.join(failed_deps)}. " + " | ".join(
            details_parts
        )
    else:
        status = "pass"
        error_code = None
        details = "All critical dependencies satisfied. " + " | ".join(details_parts)

    return PreflightCheck(
        name=check_name,
        check_type=check_type,
        status=status,
        details=details,
        timestamp=datetime.now(),
        error_code=error_code,
    )


def _check_mlx_integrity() -> tuple[str, str]:
    """Check MLX and mlx-lm are installed and compatible.

    Returns:
        Tuple of (status, details)
    """
    try:
        import importlib.metadata

        try:
            mlx_lm_version = importlib.metadata.version("mlx-lm")
            mlx_version = importlib.metadata.version("mlx")

            # Check minimum version
            min_version = "0.19.0"
            if _version_compare(mlx_lm_version, min_version) >= 0:
                return "pass", f"mlx-lm {mlx_lm_version}, mlx {mlx_version}"
            else:
                return "fail", f"mlx-lm {mlx_lm_version} (minimum: {min_version})"

        except importlib.metadata.PackageNotFoundError as e:
            return "fail", f"mlx-lm not found: {str(e)}"

    except ImportError:
        return "fail", "Cannot import importlib.metadata"


def _check_psutil_available() -> tuple[str, str]:
    """Check if psutil is available.

    Returns:
        Tuple of (status, details)
    """
    try:
        import psutil

        return "pass", f"psutil {psutil.__version__}"
    except ImportError:
        return "fail", "psutil not installed"


def _check_turboquant_available() -> tuple[str, str]:
    """Check if TurboQuant is available (non-critical).

    Returns:
        Tuple of (status, details)
    """
    try:
        import turboquant_mlx

        return "pass", "TurboQuant available"
    except ImportError:
        return "warning", "TurboQuant not available (optional)"


def _check_kv_cache_support() -> tuple[str, str]:
    """Verify KV cache compression support (non-critical).

    Returns:
        Tuple of (status, details)
    """
    try:
        # Check if the KV cache module exists
        from scripts.quantization import kv_cache_compression

        return "pass", "KV cache compression supported"
    except ImportError:
        return "warning", "KV cache compression not available (optional)"


def _version_compare(v1: str, v2: str) -> int:
    """Compare two version strings.

    Returns:
        -1 if v1 < v2
         0 if v1 == v2
         1 if v1 > v2
    """
    v1_parts = [int(x) for x in v1.split(".")]
    v2_parts = [int(x) for x in v2.split(".")]

    # Pad with zeros
    max_len = max(len(v1_parts), len(v2_parts))
    v1_parts.extend([0] * (max_len - len(v1_parts)))
    v2_parts.extend([0] * (max_len - len(v2_parts)))

    for i in range(max_len):
        if v1_parts[i] < v2_parts[i]:
            return -1
        elif v1_parts[i] > v2_parts[i]:
            return 1
    return 0
