"""
Status monitoring service - polls MLX server health endpoint.

Implements health check polling contract from contracts/http-endpoints.md
"""

from datetime import datetime

import requests

from .models import ServerStatus

MLX_HEALTH_URL = "http://localhost:8000/health"
PREFLIGHT_STATUS_FILE = "/tmp/mlx-preflight-status.json"
TIMEOUT = 2  # seconds


def check_server_health() -> ServerStatus:
    """
    Check MLX server health endpoint and return status.

    Returns:
        ServerStatus with current server state
    """
    try:
        response = requests.get(MLX_HEALTH_URL, timeout=TIMEOUT)
        health_data = response.json() if response.status_code == 200 else None

        return ServerStatus(
            status="running",
            timestamp=datetime.now(),
            health_data=health_data,
            error=None,
        )
    except requests.RequestException as e:
        return ServerStatus(
            status="stopped", timestamp=datetime.now(), health_data=None, error=str(e)
        )


def get_preflight_status() -> dict:
    """
    Query preflight status from status file (T028, T026).

    Returns:
        Dict with preflight status: overall_status, checks, block_startup, degraded_mode
    """
    import json
    from pathlib import Path

    status_file = Path(PREFLIGHT_STATUS_FILE)
    if not status_file.exists():
        return {
            "overall_status": "unknown",
            "checks": [],
            "block_startup": False,
            "degraded_mode": {"active": False},
            "timestamp": None,
        }

    try:
        with open(status_file, "r") as f:
            return json.load(f)
    except Exception as e:
        return {
            "overall_status": "error",
            "checks": [],
            "block_startup": False,
            "degraded_mode": {"active": False},
            "error": str(e),
        }


def get_degraded_mode_status() -> dict:
    """
    Get degraded mode status from preflight status file (T029).

    Returns:
        Dict with degraded mode info: active, disabled_features, fallback_config
    """
    preflight = get_preflight_status()
    degraded = preflight.get("degraded_mode", {})

    return {
        "active": degraded.get("active", False),
        "disabled_features": degraded.get("disabled_features", []),
        "fallback_quantization": degraded.get("fallback_quantization"),
        "fallback_profile": degraded.get("fallback_profile"),
        "overall_status": preflight.get("overall_status", "unknown"),
    }
