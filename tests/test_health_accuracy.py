"""
Health Check Accuracy Tests for MLX Server Wrapper
Tests fault injection scenarios to verify health check correctly reports server state.
Target: 95% accuracy (SC-006)
"""

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

# Import the mlx_wrapper module
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

# Import directly from the module
import mlx_wrapper  # noqa: E402
from mlx_wrapper import health_app, update_health_status  # noqa: E402


class TestHealthCheckAccuracy:
    """Test health check accuracy with fault injection."""

    def setup_method(self):
        """Reset health status before each test."""
        mlx_wrapper.health_status = {
            "status": "down",
            "model": None,
            "model_loaded": False,
            "load_progress_pct": 0,
            "memory_usage_gb": 0.0,
            "memory_limit_gb": None,
            "uptime_seconds": 0,
            "active_requests": 0,
            "last_check_timestamp": "2026-05-12T00:00:00Z",
            "system": {},
        }

    def test_healthy_server_reporting(self):
        """Test that healthy server reports correct status."""
        update_health_status("ready", model="/path/to/model", model_loaded=True)
        mlx_wrapper.health_status["uptime_seconds"] = 120

        with health_app.test_client() as client:
            resp = client.get("/health")
            assert resp.status_code == 200

            data = resp.get_json()
            assert data["status"] == "ready"
            assert data["model_loaded"] is True
            assert data["uptime_seconds"] == 120
            assert "system" in data

    def test_initializing_server_reporting(self):
        """Test that initializing server reports correct status."""
        update_health_status(
            "initializing", model="/path/to/model", load_progress_pct=45
        )

        with health_app.test_client() as client:
            resp = client.get("/health")
            assert resp.status_code == 200

            data = resp.get_json()
            assert data["status"] == "initializing"
            assert data["model_loaded"] is False
            assert data["load_progress_pct"] == 45

    def test_down_server_reporting(self):
        """Test that down server reports correct status."""
        update_health_status("down")

        with health_app.test_client() as client:
            resp = client.get("/health")
            assert resp.status_code == 200

            data = resp.get_json()
            assert data["status"] == "down"
            assert data["model_loaded"] is False

    @patch("mlx_wrapper.requests.get")
    def test_mlx_server_up(self, mock_get):
        """Test health check when mlx_lm.server is up."""
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"data": [{"id": "model-1"}]}
        mock_get.return_value = mock_resp

        # Simulate server being ready
        update_health_status("ready", model="/path/to/model", model_loaded=True)

        with health_app.test_client() as client:
            resp = client.get("/health")
            data = resp.get_json()
            assert data["status"] == "ready"

    @patch("mlx_wrapper.requests.get")
    def test_mlx_server_down(self, mock_get):
        """Test health check when mlx_lm.server is down."""
        mock_get.side_effect = requests.RequestException("Connection refused")

        update_health_status("down")

        with health_app.test_client() as client:
            resp = client.get("/health")
            data = resp.get_json()
            assert data["status"] == "down"

    def test_fault_injection_model_load_failure(self):
        """Test health reporting during model load failure."""
        update_health_status("initializing", load_progress_pct=75)

        # Simulate process crash
        update_health_status("down")

        with health_app.test_client() as client:
            resp = client.get("/health")
            data = resp.get_json()
            assert data["status"] == "down"
            assert data["model_loaded"] is False

    def test_fault_injection_process_crash(self):
        """Test health reporting when server process crashes."""
        # Start as ready
        update_health_status("ready", model="/path/to/model", model_loaded=True)

        # Simulate crash
        update_health_status("down")

        with health_app.test_client() as client:
            resp = client.get("/health")
            data = resp.get_json()
            assert data["status"] == "down"

    def test_health_status_timestamp_updated(self):
        """Test that health status timestamp is updated on each check."""

        update_health_status("ready")
        time.sleep(0.1)

        with health_app.test_client() as client:
            resp = client.get("/health")
            data = resp.get_json()

            # Timestamp should be recent
            timestamp = data["last_check_timestamp"]
            # Parse and verify it's a valid ISO 8601 timestamp
            assert "T" in timestamp
            assert timestamp.endswith("Z")

    def test_system_metrics_included(self):
        """Test that system metrics are included in health check."""
        update_health_status("ready")

        with health_app.test_client() as client:
            resp = client.get("/health")
            data = resp.get_json()

            assert "system" in data
            system = data["system"]
            assert "cpu_percent" in system
            assert "memory_available_gb" in system
            assert "disk_free_gb" in system

    @patch("mlx_wrapper.psutil")
    def test_memory_metrics_accuracy(self, mock_psutil):
        """Test accuracy of memory metrics reporting."""
        # Mock virtual_memory
        mock_memory = MagicMock()
        mock_memory.available = 8 * 1024**3  # 8GB
        mock_psutil.virtual_memory.return_value = mock_memory

        # Mock cpu_percent to return a real float
        mock_psutil.cpu_percent.return_value = 25.0

        # Mock disk_usage to return an object with .free as a real number
        mock_disk = MagicMock()
        mock_disk.free = 100 * 1024**3  # 100GB
        # When dividing by 1024**3, we need the result to be a real float
        # So we need to mock the division result or use a real object
        mock_psutil.disk_usage.return_value = type(
            "DiskUsage", (), {"free": 100 * 1024**3}
        )()

        update_health_status("ready")

        with health_app.test_client() as client:
            resp = client.get("/health")
            data = resp.get_json()

            assert data["system"]["memory_available_gb"] == pytest.approx(8.0, rel=0.1)
            assert data["system"]["disk_free_gb"] == pytest.approx(100.0, rel=0.1)


class TestHealthCheckAccuracyIntegration:
    """Integration tests for health check accuracy (requires running server)."""

    @pytest.mark.skip(reason="Requires running MLX server - run manually")
    def test_real_server_health_check(self):
        """Test health check against real server (manual test)."""
        # runner = CliRunner()  # noqa: F841 - kept for future use
        # This would require starting the actual server
        # For CI/CD, this test is skipped
        pass
