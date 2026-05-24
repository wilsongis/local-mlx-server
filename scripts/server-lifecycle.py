#!/usr/bin/env python3
"""
Server Lifecycle Management for MLX Server.

Provides PID file management, port conflict detection, health checking,
and graceful shutdown capabilities for the local MLX inference server.
"""

import fcntl
import json
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional

import psutil
import requests

# Configure logging
logger = logging.getLogger("server-lifecycle")


class ServerLifecycleManager:
    """Manages MLX server lifecycle: start, stop, status with PID file management."""

    def __init__(
        self,
        pid_file: str = "/tmp/mlx-server.pid",
        log_level: str = "INFO",
        graceful_timeout: int = 30,
    ):
        self.pid_file = Path(pid_file)
        self.graceful_timeout = graceful_timeout
        self._setup_logging(log_level)

    def _setup_logging(self, log_level: str) -> None:
        """Configure structured lifecycle logging (FR-010)."""
        level = getattr(logging, log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # ------------------------------------------------------------------
    # PID File Management (T002, T003)
    # ------------------------------------------------------------------

    def create_pid_file(self, pid: int) -> bool:
        """Atomically create PID file with file locking to prevent corruption."""
        try:
            with open(self.pid_file, "w") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                f.write(str(pid))
                f.flush()
                os.fsync(f.fileno())
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            logger.info(f"Created PID file {self.pid_file} with PID {pid}")
            return True
        except (IOError, OSError) as e:
            logger.error(f"Failed to create PID file: {e}")
            return False

    def read_pid_file(self) -> Optional[int]:
        """Read and validate PID from PID file."""
        if not self.pid_file.exists():
            return None
        try:
            with open(self.pid_file, "r") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                content = f.read().strip()
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            pid = int(content)
            return pid
        except (IOError, OSError, ValueError) as e:
            logger.warning(f"Failed to read PID file: {e}")
            return None

    def remove_pid_file(self) -> bool:
        """Remove PID file if it exists."""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
                logger.info(f"Removed PID file {self.pid_file}")
            return True
        except OSError as e:
            logger.error(f"Failed to remove PID file: {e}")
            return False

    # ------------------------------------------------------------------
    # Process Validation (T004)
    # ------------------------------------------------------------------

    def is_process_alive(self, pid: int) -> bool:
        """Check if a process with given PID is alive using psutil."""
        try:
            process = psutil.Process(pid)
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False

    def validate_pid_file(self) -> tuple[Optional[int], bool]:
        """
        Validate PID file: read PID, check if process is alive.
        Returns (pid, is_valid) tuple.
        """
        pid = self.read_pid_file()
        if pid is None:
            return None, False
        if self.is_process_alive(pid):
            return pid, True
        else:
            logger.warning(f"Stale PID file detected (PID {pid} not running)")
            return pid, False

    def cleanup_stale_pid(self) -> bool:
        """Remove stale PID file if process is not running."""
        pid, is_valid = self.validate_pid_file()
        if pid is not None and not is_valid:
            logger.info(f"Cleaning up stale PID file for PID {pid}")
            return self.remove_pid_file()
        return True

    # ------------------------------------------------------------------
    # Port Conflict Detection (T005)
    # ------------------------------------------------------------------

    def is_port_in_use(
        self, port: int, host: str = "127.0.0.1"
    ) -> tuple[bool, Optional[int]]:
        """
        Check if port is in use. Returns (in_use, conflicting_pid).
        Uses psutil for cross-platform port detection.
        """
        for conn in psutil.net_connections(kind="inet"):
            try:
                laddr = conn.laddr
                if laddr and hasattr(laddr, "port") and laddr.port == port:
                    if conn.status == psutil.CONN_LISTEN:
                        return True, conn.pid
            except (AttributeError, ValueError):
                continue
        return False, None

    def find_available_port(
        self, start_port: int = 8080, scan_depth: int = 10
    ) -> Optional[int]:
        """Find next available port in range (T021, T022)."""
        for port in range(start_port, start_port + scan_depth):
            in_use, _ = self.is_port_in_use(port)
            if not in_use:
                logger.info(f"Found available port: {port}")
                return port
        logger.warning(
            f"No available port found in range {start_port}-{start_port + scan_depth - 1}"
        )
        return None

    # ------------------------------------------------------------------
    # Health Endpoint Checker (T006)
    # ------------------------------------------------------------------

    def check_health(
        self, port: int = 8080, host: str = "127.0.0.1", timeout: int = 5
    ) -> dict[str, Any]:
        """
        Query /health endpoint and return status dict.
        Returns: {"healthy": bool, "status": str, "response": dict}
        """
        url = f"http://{host}:{port}/health"
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return {
                    "healthy": True,
                    "status": "healthy",
                    "response": response.json(),
                }
            else:
                return {
                    "healthy": False,
                    "status": f"http_{response.status_code}",
                    "response": None,
                }
        except requests.RequestException as e:
            return {"healthy": False, "status": "unreachable", "response": str(e)}

    # ------------------------------------------------------------------
    # Server Start (T007-T010)
    # ------------------------------------------------------------------

    def start_server(
        self,
        model_path: str,
        port: int = 8080,
        host: str = "127.0.0.1",
        extra_args: Optional[list] = None,
        kv_cache_config: Optional[dict] = None,
    ) -> bool:
        """
        Start MLX server with PID management.
        Returns True if server started successfully.
        If model_path is not provided (empty string), reads from active model state file.
        """
        # If no model path provided, check for active model
        if not model_path:
            state_file = Path(__file__).parent.parent / ".active-model"
            if state_file.exists():
                try:
                    with open(state_file, "r") as f:
                        active_profile = f.read().strip()
                        if active_profile:
                            # Look up profile in registry to get model path
                            from scripts.model_management import ModelRegistry

                            registry = ModelRegistry()
                            profile = registry.get_profile(active_profile)
                            if profile:
                                model_path = profile.model_path
                                logger.info(
                                    f"Using active model profile: {active_profile} ({model_path})"
                                )
                            else:
                                logger.warning(
                                    f"Active profile '{active_profile}' not found in registry"
                                )
                        else:
                            logger.error(
                                "No active model set. Use 'just model-use <profile>' to set one."
                            )
                            return False
                except Exception as e:
                    logger.error(f"Failed to read active model: {e}")
                    return False
            else:
                logger.error("No model path provided and no active model set.")
                logger.error("Use 'just model-use <profile>' to set an active model.")
                return False

        # Check for existing PID file
        pid, is_valid = self.validate_pid_file()
        if is_valid:
            logger.error(f"Server already running with PID {pid}")
            return False

        # Clean up stale PID if present
        self.cleanup_stale_pid()

        # Check port conflict
        in_use, conflicting_pid = self.is_port_in_use(port)
        if in_use:
            logger.error(f"Port {port} already in use by PID {conflicting_pid}")
            return False

        # Build command
        # Build command - use wrapper script to enable KV cache compression
        wrapper_script = str(Path(__file__).parent / "mlx_server_wrapper.py")
        cmd = [
            "python",
            wrapper_script,
            "--model",
            model_path,
            "--port",
            str(port),
            "--host",
            host,
        ]

        # Set environment variables for KV cache compression
        env = os.environ.copy()

        if kv_cache_config:
            from scripts.quantization.quantization_manager import QuantizationManager

            # Create quantization manager with KV cache config
            qm = QuantizationManager(
                model_path=model_path,
                kv_cache_config=kv_cache_config,
            )
            qm.initialize()

            # Set environment variables for wrapper script
            env["KV_CACHE_ENABLED"] = "true"
            env["KV_CACHE_PROFILE"] = kv_cache_config.get("profile", "auto")
            env["KV_CACHE_BITS"] = str(kv_cache_config.get("default_bits", 3))
            env["KV_CACHE_GROUP_SIZE"] = str(
                kv_cache_config.get("default_group_size", 64)
            )

            # Get quantization args
            quant_args = qm.get_quantization_args()
            if quant_args and "--quant-config" in quant_args:
                cmd.extend(["--quant-config", quant_args["--quant-config"]])

            logger.info(
                f"KV cache compression enabled: {kv_cache_config.get('profile', 'auto')}"
            )
        if extra_args:
            cmd.extend(extra_args)

        logger.info(f"Starting server: {' '.join(cmd)}")

        try:
            # Start server in background
            # Start server in background with environment variables
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
                env=env if kv_cache_config else None,
            )
            pid = process.pid

            # Create PID file
            if not self.create_pid_file(pid):
                process.terminate()
                return False

            logger.info(f"Server started with PID {pid}")
            return True

        except (subprocess.SubprocessError, OSError) as e:
            logger.error(f"Failed to start server: {e}")
            return False

    # ------------------------------------------------------------------
    # Server Stop (T011-T015)
    # ------------------------------------------------------------------

    def stop_server(self) -> bool:
        """
        Stop server with graceful shutdown (SIGTERM, wait, SIGKILL).
        Returns True if server stopped successfully.
        """
        pid, is_valid = self.validate_pid_file()
        if not is_valid:
            logger.info("No running server found")
            self.cleanup_stale_pid()
            return True

        if pid is None:
            logger.info("No PID found")
            return True

        logger.info(
            f"Stopping server with PID {pid} (graceful timeout: {self.graceful_timeout}s)"
        )

        try:
            # Send SIGTERM for graceful shutdown
            os.kill(pid, signal.SIGTERM)
            logger.info(f"Sent SIGTERM to PID {pid}")
        except OSError as e:
            logger.error(f"Failed to send SIGTERM: {e}")
            return False

        # Wait for graceful shutdown
        start_time = time.time()
        while time.time() - start_time < self.graceful_timeout:
            if not self.is_process_alive(pid):
                logger.info("Server stopped gracefully")
                self.remove_pid_file()
                return True

            # Check if health endpoint is still responding (request draining)
            # Note: True request draining requires mlx_lm.server wrapper integration
            time.sleep(0.5)

        # Timeout: send SIGKILL
        logger.warning(
            f"Graceful shutdown timeout exceeded, sending SIGKILL to PID {pid}"
        )
        try:
            os.kill(pid, signal.SIGKILL)
            time.sleep(1)
            if not self.is_process_alive(pid):
                logger.info("Server killed")
                self.remove_pid_file()
                return True
        except OSError as e:
            logger.error(f"Failed to send SIGKILL: {e}")

        return False

    # ------------------------------------------------------------------
    # Server Status (T016-T019.1)
    # ------------------------------------------------------------------

    def get_status(self, port: int = 8080, host: str = "127.0.0.1") -> dict[str, Any]:
        """
        Get comprehensive server status.
        Returns dict with keys: running, pid, uptime, port, health, status
        """
        pid, is_valid = self.validate_pid_file()

        status: dict[str, Any] = {
            "running": False,
            "pid": None,
            "uptime": None,
            "port": port,
            "health": None,
            "status": "stopped",
        }

        if not is_valid:
            if pid is not None:
                status["status"] = "stale_pid"
                status["pid"] = pid
            return status

        # Server is running
        if pid is None:
            return status

        status["running"] = True
        status["pid"] = pid

        # Calculate uptime
        try:
            process = psutil.Process(pid)
            create_time = process.create_time()
            uptime_seconds = time.time() - create_time
            status["uptime"] = int(uptime_seconds)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            status["status"] = "zombie"
            return status

        # Check health endpoint
        health = self.check_health(port, host)
        status["health"] = health

        if isinstance(health, dict) and health.get("healthy"):
            status["status"] = "healthy"
        else:
            status["status"] = "degraded"

        return status

    def format_status(self, status: dict[str, Any]) -> str:
        """Format status dict into human-readable output."""
        lines = []
        lines.append(f"Server Status: {status['status'].upper()}")

        if status["running"]:
            lines.append(f"  PID: {status['pid']}")
            if status["uptime"] is not None:
                uptime_min = status["uptime"] // 60
                lines.append(f"  Uptime: {uptime_min} minutes")
            lines.append(f"  Port: {status['port']}")
            if status["health"]:
                health_dict = status["health"]
                if isinstance(health_dict, dict):
                    lines.append(f"  Health: {health_dict.get('status', 'unknown')}")

        return "\n".join(lines)


# ------------------------------------------------------------------
# CLI Entry Points
# ------------------------------------------------------------------


def main() -> None:
    """CLI entry point for server lifecycle management."""
    import argparse

    parser = argparse.ArgumentParser(description="MLX Server Lifecycle Manager")
    parser.add_argument(
        "--pid-file", default="/tmp/mlx-server.pid", help="Path to PID file"
    )
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    parser.add_argument(
        "--graceful-timeout", type=int, default=30, help="Graceful shutdown timeout"
    )

    subparsers = parser.add_subparsers(dest="command")

    # start
    start_parser = subparsers.add_parser("start", help="Start server")
    start_parser.add_argument("--model", required=True, help="Model path")
    start_parser.add_argument("--port", type=int, default=8080, help="Server port")
    start_parser.add_argument("--host", default="127.0.0.1", help="Server host")

    # stop
    subparsers.add_parser("stop", help="Stop server")

    # status
    status_parser = subparsers.add_parser("status", help="Check server status")
    status_parser.add_argument("--port", type=int, default=8080, help="Server port")
    status_parser.add_argument("--host", default="127.0.0.1", help="Server host")
    status_parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    manager = ServerLifecycleManager(
        pid_file=args.pid_file,
        log_level=args.log_level,
        graceful_timeout=args.graceful_timeout,
    )

    if args.command == "start":
        if not hasattr(args, "model") or not args.model:
            print("Error: --model required for start command", file=sys.stderr)
            sys.exit(1)
        success = manager.start_server(
            model_path=args.model, port=args.port, host=args.host
        )
        sys.exit(0 if success else 1)

    elif args.command == "stop":
        success = manager.stop_server()
        sys.exit(0 if success else 1)

    elif args.command == "status":
        status = manager.get_status(port=args.port, host=args.host)
        if hasattr(args, "json") and args.json:
            print(json.dumps(status, indent=2))
        else:
            print(manager.format_status(status))
        sys.exit(0)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
