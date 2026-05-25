"""
MLX Server Admin GUI - Flask Application Entry Point

Implements the main dashboard with server status, model info, and controls.
Follows the implementation plan from specs/009-admin-gui-mvp/plan.md
"""

from datetime import datetime

from flask import Flask, jsonify, render_template

from gui.services.log_reader import read_logs
from gui.services.server_control import run_just_command
from gui.services.status_monitor import check_server_health, get_degraded_mode_status

app = Flask(__name__)

MLX_HEALTH_URL = "http://localhost:8000/health"
GUI_PORT = 3000


@app.route("/")
def index():
    """Main dashboard page displaying server status, model info, and controls."""
    status = check_server_health()

    model_info = None
    model_quantization = None
    if status.health_data and status.status == "running":
        model_info = status.health_data.get("model")
        model_quantization = status.health_data.get("quantization")

    # Get degraded mode status
    degraded_status = get_degraded_mode_status()
    
    return render_template(
        "index.html",
        server_status=status.status,
        model_info=model_info,
        model_quantization=model_quantization,
        last_checked=status.timestamp.isoformat(),
        error=status.error,
        degraded_mode_active=degraded_status["active"],
        degraded_disabled_features=degraded_status["disabled_features"],
        degraded_fallback_quantization=degraded_status["fallback_quantization"],
        degraded_fallback_profile=degraded_status["fallback_profile"],
    )


@app.route("/api/status")
def api_status():
    """JSON endpoint for polling server status."""
    status = check_server_health()

    result = {
        "status": status.status,
        "timestamp": status.timestamp.isoformat(),
        "model": None,
        "error": status.error,
    }

    if status.health_data and status.status == "running":
        result["model"] = {
            "name": status.health_data.get("model"),
            "quantization_config": status.health_data.get("quantization"),
        }

    return jsonify(result)


@app.route("/api/start", methods=["POST"])
def api_start():
    """Trigger server start via just start command."""
    try:
        success, message, error = run_just_command("start")
        return jsonify(
            {
                "success": success,
                "message": message
                or (
                    "Server started successfully"
                    if success
                    else "Failed to start server"
                ),
                "error": error if not success else None,
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        return jsonify(
            {
                "success": False,
                "message": f"Unexpected error: {str(e)}",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
        ), 500


@app.route("/api/stop", methods=["POST"])
def api_stop():
    """Trigger server stop via just stop command."""
    try:
        success, message, error = run_just_command("stop")
        return jsonify(
            {
                "success": success,
                "message": message
                or (
                    "Server stopped successfully"
                    if success
                    else "Failed to stop server"
                ),
                "error": error if not success else None,
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        return jsonify(
            {
                "success": False,
                "message": f"Unexpected error: {str(e)}",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
        ), 500


@app.route("/logs")
def logs():
    """Log viewer page displaying recent server log output."""
    log_entries = read_logs()
    status = check_server_health()

    return render_template(
        "logs.html",
        log_entries=log_entries,
        server_running=(status.status == "running"),
    )


if __name__ == "__main__":
    app.run(host="localhost", port=GUI_PORT, debug=True)
