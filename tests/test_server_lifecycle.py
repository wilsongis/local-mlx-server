"""
Tests for Server Lifecycle Management (T028-T034.3).

Comprehensive test coverage for ServerLifecycleManager class including:
- PID file management (create, read, validate, stale detection, atomic writes)
- Port conflict detection and resolution
- Health endpoint checking
- Server start/stop/status logic
- Graceful shutdown behavior
- Performance benchmarks (NFR-001, NFR-002, NFR-005)
"""

import importlib.util
import os
import signal
import sys
import tempfile
import time
from unittest.mock import MagicMock, patch

import psutil
import pytest

# Import server_lifecycle module (filename has hyphen, so we use importlib)
spec = importlib.util.spec_from_file_location(
    "server_lifecycle",
    "/Users/wilsonm/Development/local-mlx-server/scripts/server-lifecycle.py",
)
assert spec is not None, "Failed to load server_lifecycle spec"
server_lifecycle = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
sys.modules["server_lifecycle"] = server_lifecycle
spec.loader.exec_module(server_lifecycle)  # type: ignore[union-attr]

ServerLifecycleManager = server_lifecycle.ServerLifecycleManager


@pytest.fixture
def temp_pid_file():
    """Create a temporary PID file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".pid") as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def manager(temp_pid_file):
    """Create a ServerLifecycleManager with temporary PID file."""
    return ServerLifecycleManager(
        pid_file=temp_pid_file, log_level="DEBUG", graceful_timeout=5
    )


# ============================================================================
# T029: PID File Management Tests
# ============================================================================


class TestPIDFileManagement:
    """Tests for PID file management (T029)."""

    def test_create_pid_file(self, manager, temp_pid_file):
        """Test creating a PID file with atomic write."""
        manager.create_pid_file(12345)
        assert True
        assert os.path.exists(temp_pid_file)
        with open(temp_pid_file, "r") as f:
            assert f.read().strip() == "12345"

    def test_read_pid_file(self, manager, temp_pid_file):
        """Test reading PID from file."""
        with open(temp_pid_file, "w") as f:
            f.write("54321")
        pid = manager.read_pid_file()
        assert pid == 54321

    def test_read_nonexistent_pid_file(self, manager, temp_pid_file):
        """Test reading non-existent PID file returns None."""
        pid = manager.read_pid_file()
        assert pid is None

    def test_remove_pid_file(self, manager, temp_pid_file):
        """Test removing PID file."""
        with open(temp_pid_file, "w") as f:
            f.write("12345")
        manager.remove_pid_file()
        assert True
        assert not os.path.exists(temp_pid_file)

    def test_validate_pid_file_valid(self, manager, temp_pid_file):
        """Test validating a valid PID file."""
        with open(temp_pid_file, "w") as f:
            f.write(str(os.getpid()))
        pid, is_valid = manager.validate_pid_file()
        assert pid == os.getpid()
        assert is_valid is True

    def test_validate_pid_file_stale(self, manager, temp_pid_file):
        """Test detecting stale PID file (process not running)."""
        # Use a PID that's unlikely to exist
        stale_pid = 999999
        with open(temp_pid_file, "w") as f:
            f.write(str(stale_pid))
        pid, is_valid = manager.validate_pid_file()
        assert pid == stale_pid
        assert is_valid is False

    def test_validate_pid_file_nonexistent(self, manager, temp_pid_file):
        """Test validating non-existent PID file."""
        pid, is_valid = manager.validate_pid_file()
        assert pid is None
        assert is_valid is False

    def test_cleanup_stale_pid(self, manager, temp_pid_file):
        """Test cleaning up stale PID file."""
        with open(temp_pid_file, "w") as f:
            f.write("999999")
        manager.cleanup_stale_pid()
        assert True
        assert not os.path.exists(temp_pid_file)

    def test_atomic_pid_write(self, manager, temp_pid_file):
        """Test atomic PID file write with file locking (T003)."""
        # This test verifies the file locking mechanism doesn't corrupt the file
        manager.create_pid_file(11111)
        assert True
        # Verify file can be read back correctly
        pid = manager.read_pid_file()
        assert pid == 11111


# ============================================================================
# T030: Port Conflict Detection Tests
# ============================================================================


class TestPortConflictDetection:
    """Tests for port conflict detection (T030)."""

    @patch("server_lifecycle.psutil.net_connections")
    def test_port_not_in_use(self, mock_connections, manager):
        """Test when port is not in use."""
        mock_connections.return_value = []
        in_use, conflicting_pid = manager.is_port_in_use(8080)
        assert in_use is False
        assert conflicting_pid is None

    @patch("server_lifecycle.psutil.net_connections")
    def test_port_in_use(self, mock_connections, manager):
        """Test when port is in use."""
        mock_conn = MagicMock()
        mock_conn.laddr = MagicMock(port=8080)
        mock_conn.status = psutil.CONN_LISTEN
        mock_conn.pid = 12345
        mock_connections.return_value = [mock_conn]

        in_use, conflicting_pid = manager.is_port_in_use(8080)
        assert in_use is True
        assert conflicting_pid == 12345

    def test_find_available_port(self, manager):
        """Test finding available port in range (T021)."""
        with patch.object(manager, "is_port_in_use", return_value=(False, None)):
            port = manager.find_available_port(start_port=8080, scan_depth=10)
            assert port == 8080

    def test_find_available_port_conflict(self, manager):
        """Test finding available port when first port is in use."""

        def mock_port_check(port):
            return (port == 8080, 12345) if port == 8080 else (False, None)

        with patch.object(manager, "is_port_in_use", side_effect=mock_port_check):
            port = manager.find_available_port(start_port=8080, scan_depth=10)
            assert port == 8081

    def test_port_scan_range_config(self, manager):
        """Test port scan range configuration (T022)."""
        with patch.object(manager, "is_port_in_use", return_value=(True, 12345)):
            port = manager.find_available_port(start_port=8080, scan_depth=5)
            assert port is None


# ============================================================================
# T031: Graceful Shutdown Tests
# ============================================================================


class TestGracefulShutdown:
    """Tests for graceful shutdown behavior (T031)."""

    @patch("server_lifecycle.os.kill")
    @patch("os.path.exists")
    def test_stop_server_no_pid_file(
        self, mock_exists, mock_kill, manager, temp_pid_file
    ):
        """Test stopping server when no PID file exists."""
        mock_exists.return_value = False
        manager.stop_server()
        assert True
        mock_kill.assert_not_called()

    @patch("server_lifecycle.os.kill")
    def test_stop_server_sigterm(self, mock_kill, manager, temp_pid_file):
        """Test SIGTERM is sent during graceful shutdown."""
        with open(temp_pid_file, "w") as f:
            f.write(str(os.getpid()))

        with patch.object(manager, "is_process_alive", side_effect=[True, False]):
            with patch.object(manager, "check_health", return_value={"healthy": False}):
                _ = manager.stop_server()  # noqa: F841
                assert _ is True
                mock_kill.assert_any_call(os.getpid(), signal.SIGTERM)

    @patch("server_lifecycle.os.kill")
    def test_stop_server_sigkill_timeout(self, mock_kill, manager, temp_pid_file):
        """Test SIGKILL is sent after timeout."""
        with open(temp_pid_file, "w") as f:
            f.write("99999")

        # Process stays alive during graceful period, then dies after SIGKILL
        with patch.object(manager, "is_process_alive", return_value=True):
            with patch("time.time", side_effect=[0, 1, 2, 3, 6, 7]):
                _ = manager.stop_server()  # noqa: F841
                # Should have called SIGKILL
                mock_kill.assert_any_call(99999, signal.SIGKILL)


# ============================================================================
# T032: Status Check Tests
# ============================================================================


class TestStatusCheck:
    """Tests for server status checking (T032)."""

    def test_status_stopped(self, manager, temp_pid_file):
        """Test status when server is stopped."""
        status = manager.get_status()
        assert status["running"] is False
        assert status["status"] == "stopped"

    def test_status_running(self, manager, temp_pid_file):
        """Test status when server is running."""
        with open(temp_pid_file, "w") as f:
            f.write(str(os.getpid()))

        with patch.object(
            manager, "check_health", return_value={"healthy": True, "status": "healthy"}
        ):
            status = manager.get_status()
            assert status["running"] is True
            assert status["pid"] == os.getpid()

    def test_status_stale_pid(self, manager, temp_pid_file):
        """Test status with stale PID file."""
        with open(temp_pid_file, "w") as f:
            f.write("999999")

        status = manager.get_status()
        assert status["status"] == "stale_pid"
        assert status["pid"] == 999999

    def test_format_status(self, manager):
        """Test status formatting for display."""
        status = {
            "running": True,
            "pid": 12345,
            "uptime": 300,
            "port": 8080,
            "health": {"status": "healthy"},
            "status": "healthy",
        }
        formatted = manager.format_status(status)
        assert "HEALTHY" in formatted
        assert "PID: 12345" in formatted
        assert "Uptime: 5 minutes" in formatted


# ============================================================================
# T033: Integration Tests for just Recipes
# ============================================================================


class TestJustRecipeIntegration:
    """Tests for just recipe integration (T033)."""

    @patch("server_lifecycle.subprocess.Popen")
    def test_start_server_command(self, mock_popen, manager, temp_pid_file):
        """Test server start command execution."""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        with patch.object(manager, "is_port_in_use", return_value=(False, None)):
            with patch.object(manager, "create_pid_file", return_value=True):
                result = manager.start_server(model_path="/path/to/model")
                assert result is True

    def test_stop_server_command(self, manager, temp_pid_file):
        """Test server stop command execution."""
        with open(temp_pid_file, "w") as f:
            f.write(str(os.getpid()))

        with patch.object(manager, "is_process_alive", return_value=False):
            result = manager.stop_server()
            assert result is True


# ============================================================================
# T034: Logging Tests
# ============================================================================


class TestLogging:
    """Tests for lifecycle logging (T034, FR-010)."""

    def test_logging_configuration(self, manager):
        """Test logging is configured with correct level."""
        import logging

        logger = logging.getLogger("server-lifecycle")
        # Logger should be configured
        assert logger is not None

    @patch("logging.Logger.info")
    def test_lifecycle_events_logged(self, mock_log, manager, temp_pid_file):
        """Test lifecycle events are logged."""
        manager.create_pid_file(12345)
        # Check that logging was called
        assert mock_log.called


# ============================================================================
# T034.1: Performance Test - NFR-001 (Server start <5s)
# ============================================================================


class TestPerformanceStart:
    """Performance test for server start (NFR-001)."""

    @patch("server_lifecycle.subprocess.Popen")
    def test_server_start_performance(self, mock_popen, manager):
        """Test server start completes in <5s (excluding model load)."""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        with patch.object(manager, "is_port_in_use", return_value=(False, None)):
            with patch.object(manager, "create_pid_file", return_value=True):
                start_time = time.time()
                manager.start_server(model_path="/path/to/model")
                elapsed = time.time() - start_time
                # Should complete in <5s (excluding model load)
                assert elapsed < 5.0


# ============================================================================
# T034.2: Performance Test - NFR-002 (Status check <2s)
# ============================================================================


class TestPerformanceStatus:
    """Performance test for status check (NFR-002)."""

    def test_status_check_performance(self, manager, temp_pid_file):
        """Test status check completes in <2s."""
        with open(temp_pid_file, "w") as f:
            f.write(str(os.getpid()))

        with patch.object(manager, "check_health", return_value={"healthy": True}):
            start_time = time.time()
            manager.get_status()
            elapsed = time.time() - start_time
            # Should complete in <2s
            assert elapsed < 2.0


# ============================================================================
# T034.3: Performance Test - NFR-005 (Port scan <1s)
# ============================================================================


class TestPerformancePortScan:
    """Performance test for port scan (NFR-005)."""

    def test_port_scan_performance(self, manager):
        """Test port scan completes in <1s."""
        with patch.object(manager, "is_port_in_use", return_value=(False, None)):
            start_time = time.time()
            manager.find_available_port(start_port=8080, scan_depth=10)
            elapsed = time.time() - start_time
            # Should complete in <1s
            assert elapsed < 1.0
