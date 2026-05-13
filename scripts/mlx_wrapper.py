#!/usr/bin/env python3
"""
MLX Server Wrapper
Provides unified operational interface for mlx_lm.server with startup/shutdown workflows,
health monitoring, model profile selection, and memory-optimized presets for 120B+ models.
"""

import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import psutil
import requests
import yaml
from flask import Flask, jsonify, request

# Constants
DEFAULT_CONFIG_PATH = "scripts/wrapper-config/profiles.yaml"
DEFAULT_PRESETS_PATH = "scripts/wrapper-config/presets.yaml"
DEFAULT_HEALTH_PORT = 8081
MLX_LM_SERVER_READY_TIMEOUT = 300  # 5 minutes for 120B+ models
MLX_LM_SERVER_SHUTDOWN_TIMEOUT = 30  # 30 seconds graceful shutdown

# API Key for admin endpoints (None = no auth required)
api_key = None  # type: Optional[str]


class MLXServerManager:
    """Manages mlx_lm.server process lifecycle."""

    def __init__(self, model_path: str, port: int = 8080, host: str = "127.0.1"):
        self.model_path = model_path
        self.port = port
        self.host = host
        self.process = None  # type: Optional[subprocess.Popen]
        self.pid_file = Path(f"/tmp/mlx-wrapper-{port}.pid")
        self.progress_thread = None  # type: Optional[threading.Thread]

    def start(self, extra_args: Optional[Dict[str, Any]] = None) -> bool:
        """Start mlx_lm.server with given configuration."""
        cmd = [
            sys.executable,
            "-m",
            "mlx_lm.server",
            "--model",
            self.model_path,
            "--host",
            self.host,
            "--port",
            str(self.port),
        ]

        # Add extra arguments (from profile/preset)
        if extra_args:
            for key, value in extra_args.items():
                if value is not None:
                    cmd.extend([f"--{key.replace('_', '-')}", str(value)])

        click.echo(f"[INFO] Starting mlx_lm.server on {self.host}:{self.port}")
        click.echo(f"[INFO] Model: {self.model_path}")

        try:
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )

            # Write PID file
            with open(self.pid_file, "w") as f:
                f.write(str(self.process.pid))

            # Start progress monitoring thread
            self.progress_thread = threading.Thread(
                target=self._monitor_progress, daemon=True
            )
            self.progress_thread.start()

            return True
        except FileNotFoundError as e:
            click.echo(f"[ERROR] Command not found: {e}", err=True)
            click.echo(
                "[ERROR] Ensure mlx_lm is installed: uv pip install mlx-lm", err=True
            )
            return False
        except PermissionError as e:
            click.echo(f"[ERROR] Permission denied: {e}", err=True)
            return False
        except Exception as e:
            click.echo(f"[ERROR] Failed to start server: {e}", err=True)
            return False

    def _monitor_progress(self):
        """Monitor subprocess output for model loading progress."""
        if not self.process or not self.process.stdout:
            return

        try:
            for line in self.process.stdout:
                line = line.strip()
                if not line:
                    continue

                # Parse progress indicators
                progress_match = re.search(r"(\d+)%", line)
                if progress_match:
                    pct = int(progress_match.group(1))
                    click.echo(f"[PROGRESS] Loading model... {pct}%")
                    update_health_status("initializing", load_progress_pct=pct)

                # Log other relevant output
                elif any(
                    keyword in line.lower()
                    for keyword in ["error", "failed", "exception", "traceback"]
                ):
                    click.echo(f"[SERVER ERROR] {line}", err=True)
                elif self._is_verbose():
                    click.echo(f"[SERVER] {line}")

        except (ValueError, OSError):
            pass

    def _is_verbose(self) -> bool:
        """Check if verbose mode is enabled."""
        return "--verbose" in sys.argv or "-v" in sys.argv

    def stop(
        self, force: bool = False, timeout: int = MLX_LM_SERVER_SHUTDOWN_TIMEOUT
    ) -> bool:
        """Stop the mlx_lm.server gracefully (or force kill)."""
        if not self.process and self.pid_file.exists():
            try:
                with open(self.pid_file, "r") as f:
                    pid = int(f.read().strip())
                self.process = psutil.Process(pid)
            except (FileNotFoundError, ValueError, psutil.NoSuchProcess):
                click.echo("[WARN] No running server found", err=True)
                return False

        if not self.process:
            click.echo("[WARN] No running server found", err=True)
            return False

        try:
            if force:
                self.process.kill()
                click.echo("[INFO] Force killed server")
            else:
                self.process.terminate()
                click.echo("[INFO] Sent SIGTERM, waiting for graceful shutdown...")

                try:
                    self.process.wait(timeout=timeout)
                    click.echo("[INFO] Server stopped gracefully")
                except subprocess.TimeoutExpired:
                    if not force:
                        click.echo(
                            f"[WARN] Server did not stop within {timeout}s, sending SIGKILL"
                        )
                        self.process.kill()
                        self.process.wait()

            # Clean up PID file
            if self.pid_file.exists():
                self.pid_file.unlink()

            return True
        except Exception as e:
            click.echo(f"[ERROR] Failed to stop server: {e}", err=True)
            return False

    def is_running(self) -> bool:
        """Check if server process is running."""
        if self.process:
            return self.process.poll() is None
        elif self.pid_file.exists():
            try:
                with open(self.pid_file, "r") as f:
                    pid = int(f.read().strip())
                process = psutil.Process(pid)
                return process.is_running()
            except (FileNotFoundError, ValueError, psutil.NoSuchProcess):
                return False
        return False

    def wait_for_ready(self, timeout: int = MLX_LM_SERVER_READY_TIMEOUT) -> bool:
        """Wait for server to become ready by polling /v1/models endpoint."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                resp = requests.get(
                    f"http://{self.host}:{self.port}/v1/models", timeout=2
                )
                if resp.ok:
                    click.echo(
                        "[SUCCESS] Server ready at http://{self.host}:{self.port}"
                    )
                    return True
            except (requests.RequestException, ConnectionError):
                pass

            # Check if process is still running
            if self.process and self.process.poll() is not None:
                if self.process.stderr:
                    err_output = self.process.stderr.read()
                    if err_output:
                        click.echo(
                            f"[ERROR] Server process exited with error: {err_output}",
                            err=True,
                        )
                click.echo("[ERROR] Server process exited unexpectedly", err=True)
                return False

            time.sleep(5)

        click.echo(f"[ERROR] Server did not become ready within {timeout}s", err=True)
        return False


def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """Load YAML configuration file with profile definitions."""
    path = Path(config_path)
    if not path.exists():
        click.echo(f"[ERROR] Config file not found: {config_path}", err=True)
        return {}

    try:
        with open(path, "r") as f:
            config = yaml.safe_load(f)
        return config or {}
    except yaml.YAMLError as e:
        click.echo(f"[ERROR] Failed to parse YAML config: {e}", err=True)
        return {}


def load_presets(presets_path: str = DEFAULT_PRESETS_PATH) -> Dict[str, Any]:
    """Load YAML presets file."""
    path = Path(presets_path)
    if not path.exists():
        return {}

    try:
        with open(path, "r") as f:
            presets = yaml.safe_load(f)
        return presets or {}
    except yaml.YAMLError as e:
        click.echo(f"[WARN] Failed to parse presets file: {e}")
        return {}


def get_profile(config: Dict[str, Any], profile_name: str) -> Optional[Dict[str, Any]]:
    """Get a specific profile by name from config."""
    profiles = config.get("profiles", [])
    for profile in profiles:
        if profile.get("name") == profile_name:
            return profile
    return None


def get_preset(presets: Dict[str, Any], preset_name: str) -> Optional[Dict[str, Any]]:
    """Get a specific preset by name."""
    preset_list = presets.get("presets", [])
    for preset in preset_list:
        if preset.get("name") == preset_name:
            return preset
    return None


def validate_profile(profile: Dict[str, Any]) -> List[str]:
    """Validate a profile and return list of errors."""
    errors = []

    if "name" not in profile:
        errors.append("Profile missing 'name' field")

    model_path = profile.get("model_path")
    if not model_path:
        errors.append("Profile missing 'model_path'")
    else:
        expanded_path = Path(model_path).expanduser()
        if not expanded_path.exists():
            errors.append(f"Model path does not exist: {expanded_path}")

    quantization = profile.get("quantization", {})
    if quantization.get("type") == "hybrid":
        paths = quantization.get("paths", [])
        if not paths:
            errors.append("Hybrid quantization requires 'paths' array")

    return errors


def check_available_memory() -> float:
    """Check available system memory in GB using psutil."""
    try:
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        return available_gb
    except Exception as e:
        click.echo(f"[WARN] Failed to check memory: {e}")
        return 0.0


def build_mlx_args_from_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Build mlx_lm.server arguments from profile configuration."""
    args = {}

    # Quantization arguments
    quantization = profile.get("quantization", {})
    if quantization.get("type") == "hybrid":
        paths = quantization.get("paths", [])
        quantize_args = []
        for path in paths:
            pattern = path.get("pattern", "")
            bits = path.get("bits", 4)
            group_size = path.get("group_size", 64)
            quantize_args.append(f"{pattern}:{bits}:{group_size}")
        if quantize_args:
            args["quantize"] = ",".join(quantize_args)
    elif quantization.get("type") == "uniform":
        args["quantize"] = f"uniform:{quantization.get('bits', 4)}"

    # KV cache settings
    kv_cache = profile.get("kv_cache", {})
    if kv_cache.get("quantized"):
        args["kv_bits"] = kv_cache.get("bits", 4)

    # Inference args
    inference_args = profile.get("inference_args", {})
    args.update(inference_args)

    return args


def build_mlx_args_from_preset(
    preset: Dict[str, Any], profile_args: Dict[str, Any]
) -> Dict[str, Any]:
    """Override profile defaults with preset values."""
    args = profile_args.copy()

    if "kv_cache_bits" in preset:
        args["kv_bits"] = preset["kv_cache_bits"]

    if "max_context_length" in preset:
        args["max_context_length"] = preset["max_context_length"]

    if "batch_size" in preset:
        args["batch_size"] = preset["batch_size"]

    return args


def load_api_key(config: Dict[str, Any]) -> Optional[str]:
    """Load API key from config or environment variable (T034)."""
    global api_key

    # Check config file
    key = config.get("api_key")
    if key and key.strip():
        api_key = key.strip()
        return api_key

    # Check environment variable
    env_var = config.get("api_key_env_var", "MLX_WRAPPER_API_KEY")
    env_key = os.environ.get(env_var)
    if env_key:
        api_key = env_key
        return api_key

    api_key = None
    return None


def check_api_key() -> bool:
    """Check if request has valid API key (T035)."""
    global api_key

    # If no API key configured, allow all requests
    if not api_key:
        return True

    # Check X-API-Key header
    request_key = request.headers.get("X-API-Key")
    if request_key and request_key == api_key:
        return True

    return False


# Health endpoint server (Flask)
health_app = Flask(__name__)
health_status = {
    "status": "down",
    "model": None,
    "model_loaded": False,
    "load_progress_pct": 0,
    "memory_usage_gb": 0.0,
    "memory_limit_gb": None,
    "uptime_seconds": 0,
    "active_requests": 0,
    "last_check_timestamp": datetime.utcnow().isoformat() + "Z",
    "system": {},
}


@health_app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint returning server status and system metrics."""
    global health_status

    # Check API key for admin endpoints (T035)
    if not check_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401

    # Update system metrics
    memory = psutil.virtual_memory()
    health_status["system"] = {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_available_gb": memory.available / (1024**3),
        "disk_free_gb": psutil.disk_usage("/").free / (1024**3),
    }
    health_status["last_check_timestamp"] = datetime.utcnow().isoformat() + "Z"

    return jsonify(health_status)


def start_health_server(port: int = DEFAULT_HEALTH_PORT):
    """Start the health endpoint server in a separate thread."""
    server_thread = threading.Thread(
        target=lambda: health_app.run(host="127.0.1", port=port, debug=False),
        daemon=True,
    )
    server_thread.start()
    return server_thread


def update_health_status(status: str, model: Optional[str] = None, **kwargs):
    """Update the global health status."""
    global health_status
    health_status["status"] = status
    if model:
        health_status["model"] = model
    health_status.update(kwargs)
    health_status["last_check_timestamp"] = datetime.utcnow().isoformat() + "Z"


# CLI Commands
@click.group()
@click.option(
    "--config", default=DEFAULT_CONFIG_PATH, help="Path to YAML configuration file"
)
@click.option("--verbose", is_flag=True, help="Enable verbose/debug logging")
@click.option("--api-key", default=None, help="API key for admin endpoints (T036)")
@click.pass_context
def cli(ctx, config, verbose, api_key_option):
    """MLX Server Wrapper - Manage mlx_lm.server with profiles and presets.

    This tool provides a unified interface for managing mlx_lm.server with:
    - Profile-based configuration for different model types and quantization settings
    - Per-path hybrid quantization support for 120B+ models on Apple Silicon
    - Memory-optimized presets for constrained memory environments
    - Health monitoring with system metrics
    - API key authentication for admin endpoints (optional)

    Examples:
    \b
    mlx-wrapper --config scripts/wrapper-config/profiles.yaml start --profile 120b-balanced
    mlx-wrapper start --profile 120b-extreme --preset 120b-extreme
    mlx-wrapper --api-key my-secret list-profiles
    """
    ctx.ensure_object(dict)
    ctx.obj["config"] = config
    ctx.obj["verbose"] = verbose

    # Load API key from config first, then override with CLI option (T036)
    config_data = load_config(config)
    if config_data:
        load_api_key(config_data)

    global api_key
    if api_key_option:
        api_key = api_key_option

    if verbose:
        click.echo(f"[DEBUG] Using config: {config}")
        click.echo(f"[DEBUG] API key configured: {api_key is not None}")


@cli.command()
@click.option(
    "--profile",
    required=True,
    help="Model profile name (e.g., 120b-balanced, 120b-extreme)",
)
@click.option("--port", default=8080, help="Server port (default: 8080)")
@click.option("--host", default="127.0.1", help="Server host (default: 127.0.1)")
@click.option(
    "--preset", default=None, help="Memory optimization preset (e.g., 120b-extreme)"
)
@click.pass_context
def start(ctx, profile, port, host, preset):
    """Start MLX server with specified profile.

    Loads the specified profile from the configuration file and starts
    the mlx_lm.server with the appropriate settings.

    Example: mlx-wrapper start --profile 120b-balanced --preset 120b-extreme
    """
    config_path = ctx.obj["config"]
    config = load_config(config_path)

    if not config:
        sys.exit(1)

    # Get profile
    profile_config = get_profile(config, profile)
    if not profile_config:
        click.echo(f"[ERROR] Profile '{profile}' not found", err=True)
        click.echo(
            f"[INFO] Available profiles: {[p.get('name') for p in config.get('profiles', [])]}"
        )
        sys.exit(1)

    # Validate profile
    errors = validate_profile(profile_config)
    if errors:
        for error in errors:
            click.echo(f"[ERROR] {error}", err=True)
        sys.exit(1)

    # Build arguments from profile
    args = build_mlx_args_from_profile(profile_config)

    # Apply preset if specified
    if preset:
        presets = load_presets()
        preset_config = get_preset(presets, preset)
        if not preset_config:
            click.echo(f"[ERROR] Preset '{preset}' not found", err=True)
            sys.exit(1)
        args = build_mlx_args_from_preset(preset_config, args)

        # Check memory against preset
        available = check_available_memory()
        target = preset_config.get("target_memory_gb", 48)
        if available < target:
            click.echo(
                f"[WARN] Available memory ({available:.1f}GB) < target ({target}GB)"
            )
            click.echo("[INFO] Consider using a lower memory preset")

    # Check available memory
    available = check_available_memory()
    click.echo(f"[INFO] Available memory: {available:.1f}GB")

    # Start health server
    start_health_server()
    update_health_status("initializing", model=profile_config.get("model_path"))

    # Start MLX server
    manager = MLXServerManager(
        model_path=profile_config["model_path"], port=port, host=host
    )

    if not manager.start(extra_args=args):
        sys.exit(1)

    # Wait for ready
    if manager.wait_for_ready():
        update_health_status(
            "ready", model=profile_config.get("model_path"), model_loaded=True
        )
        click.echo(f"[SUCCESS] Server ready at http://{host}:{port}")
        click.echo(
            f"[INFO] Health endpoint: http://127.0.1:{DEFAULT_HEALTH_PORT}/health"
        )
    else:
        update_health_status("down")
        sys.exit(3)


@cli.command()
@click.option("--force", is_flag=True, help="Force kill if graceful shutdown fails")
@click.option(
    "--timeout", default=30, help="Seconds to wait for graceful shutdown (default: 30)"
)
def stop(force, timeout):
    """Stop running MLX server gracefully.

    Sends SIGTERM for graceful shutdown, with optional force kill.
    """
    manager = MLXServerManager("", 8080)  # Paths will be loaded from PID file
    success = manager.stop(force=force, timeout=timeout)
    update_health_status("down")
    sys.exit(0 if success else 1)


@cli.command()
@click.option("--json", "json_output", is_flag=True, help="Output as JSON (T030)")
def status(json_output):
    """Check server running status.

    Checks if the MLX server is currently running and reports status.
    """
    # Check if PID file exists
    pid_file = Path("/tmp/mlx-wrapper-8080.pid")
    if pid_file.exists():
        try:
            with open(pid_file, "r") as f:
                pid = int(f.read().strip())
            process = psutil.Process(pid)
            if process.is_running():
                result = {
                    "status": "running",
                    "pid": pid,
                    "port": 8080,
                }
                if json_output:
                    click.echo(json.dumps(result, indent=2))
                else:
                    click.echo(f"[INFO] Server is running (PID: {pid})")
                sys.exit(0)
        except (ValueError, psutil.NoSuchProcess):
            pass

    if json_output:
        click.echo(json.dumps({"status": "not_running"}, indent=2))
    else:
        click.echo("[INFO] Server is not running")
    sys.exit(1)


@cli.command()
@click.option("--json", "json_output", is_flag=True, help="Output as JSON (T030)")
def health(json_output):
    """Check server health via health endpoint.

    Queries the health endpoint and returns server status with system metrics.
    """
    try:
        resp = requests.get(f"http://127.0.1:{DEFAULT_HEALTH_PORT}/health", timeout=2)
        if resp.ok:
            if json_output:
                click.echo(resp.text)
            else:
                data = resp.json()
                click.echo(json.dumps(data, indent=2))
            sys.exit(0)
        else:
            click.echo(f"[ERROR] Health check failed: {resp.status_code}", err=True)
            sys.exit(1)
    except requests.RequestException as e:
        click.echo(f"[ERROR] Cannot connect to health endpoint: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def list_profiles(ctx):
    """List available model profiles.

    Shows all configured model profiles with their descriptions and model paths.
    """
    config_path = ctx.obj["config"]
    config = load_config(config_path)

    if not config:
        sys.exit(1)

    profiles = config.get("profiles", [])
    if not profiles:
        click.echo("[INFO] No profiles defined")
        return

    click.echo("Available Model Profiles:")
    click.echo("-" * 60)
    for profile in profiles:
        name = profile.get("name", "unknown")
        desc = profile.get("description", "")
        model = profile.get("model_path", "")
        click.echo(f"  {name:<20} {desc}")
        click.echo(f"    Model: {model}")


@cli.command()
def list_presets():
    """List available memory optimization presets.

    Shows all configured presets with memory targets and model size classes.
    """
    presets = load_presets()

    preset_list = presets.get("presets", [])
    if not preset_list:
        click.echo("[INFO] No presets defined")
        return

    click.echo("Available Memory Optimization Presets:")
    click.echo("-" * 60)
    for preset in preset_list:
        name = preset.get("name", "unknown")
        target = preset.get("target_memory_gb", 0)
        size_class = preset.get("model_size_class", "")
        desc = preset.get("description", "")
        click.echo(f"  {name:<20} {size_class:<10} {target:>5}GB  {desc}")


if __name__ == "__main__":
    cli()
