# Quickstart: Admin GUI MVP

**Feature**: Admin GUI MVP (009-admin-gui-mvp)
**Date**: 2026-05-24
**Status**: Complete

---

## Prerequisites

- Python 3.10+ (per `pyproject.toml`)
- `just` command runner installed (see [just installation](https://github.com/casey/just))
- MLX server dependencies installed (`uv sync` or `pip install -e .`)
- Flask (included in project dependencies)

---

## Quick Start (5 Minutes)

### 1. Navigate to Project Root

```bash
cd /Users/wilsonm/development/local-mlx-server
```

### 2. Install Dependencies (if not already done)

```bash
uv sync
# or
pip install -e .
```

### 3. Create GUI Directory Structure

```bash
mkdir -p gui/templates gui/static gui/services gui/tests
touch gui/__init__.py gui/services/__init__.py
```

### 4. Create Minimal Flask App (`gui/app.py`)

```python
from flask import Flask, render_template, jsonify
import requests
import subprocess
from datetime import datetime

app = Flask(__name__)

MLX_HEALTH_URL = "http://localhost:8000/health"
GUI_PORT = 8080

def check_server_health():
    """Check MLX server health endpoint."""
    try:
        response = requests.get(MLX_HEALTH_URL, timeout=2)
        return {
            "running": True,
            "data": response.json(),
            "timestamp": datetime.now().isoformat()
        }
    except requests.RequestException:
        return {
            "running": False,
            "data": None,
            "timestamp": datetime.now().isoformat()
        }

def run_just_command(command):
    """Run a just command and return result."""
    try:
        result = subprocess.run(
            ["just", command],
            capture_output=True,
            text=True,
            timeout=30,
            cwd="/Users/wilsonm/development/local-mlx-server"
        )
        return {
            "success": result.returncode == 0,
            "message": result.stdout.strip() or result.stderr.strip(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.route('/')
def index():
    """Main dashboard."""
    status = check_server_health()
    return render_template('index.html', 
        server_status='running' if status['running'] else 'stopped',
        model_info=status.get('data', {}).get('model') if status['running'] else None,
        last_checked=status['timestamp']
    )

@app.route('/api/status')
def api_status():
    """JSON status endpoint for polling."""
    status = check_server_health()
    result = {
        "status": "running" if status['running'] else "stopped",
        "timestamp": status['timestamp'],
        "model": None,
        "error": None
    }
    if status['running'] and status.get('data'):
        result['model'] = {
            "name": status['data'].get('model'),
            "quantization_config": status['data'].get('quantization')
        }
    return jsonify(result)

@app.route('/api/start', methods=['POST'])
def api_start():
    """Start server endpoint."""
    return jsonify(run_just_command('start'))

@app.route('/api/stop', methods=['POST'])
def api_stop():
    """Stop server endpoint."""
    return jsonify(run_just_command('stop'))

if __name__ == '__main__':
    app.run(host='localhost', port=GUI_PORT, debug=True)
```

### 5. Create Minimal Template (`gui/templates/index.html`)

```html
<!DOCTYPE html>
<html>
<head>
    <title>MLX Server Admin</title>
    <style>
        body { font-family: sans-serif; margin: 40px; }
        .status { padding: 10px; border-radius: 5px; display: inline-block; }
        .running { background: #d4edda; color: #155724; }
        .stopped { background: #f8d7da; color: #721c24; }
        button { padding: 10px 20px; margin: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>MLX Server Admin</h1>
    
    <div id="status-indicator" class="status {{ server_status }}">
        Status: {{ server_status | upper }}
    </div>
    
    {% if model_info %}
        <h2>Model Information</h2>
        <p><strong>Model:</strong> {{ model_info }}</p>
    {% endif %}
    
    <div>
        <button onclick="startServer()">Start Server</button>
        <button onclick="stopServer()">Stop Server</button>
    </div>
    
    <p><small>Last checked: {{ last_checked }}</small></p>
    
    <script>
        function startServer() {
            fetch('/api/start', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    alert(data.message);
                    setTimeout(() => location.reload(), 2000);
                });
        }
        
        function stopServer() {
            fetch('/api/stop', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    alert(data.message);
                    setTimeout(() => location.reload(), 2000);
                });
        }
        
        // Auto-refresh status every 5 seconds
        setInterval(() => location.reload(), 5000);
    </script>
</body>
</html>
```

### 6. Run the Admin GUI

```bash
cd /Users/wilsonm/development/local-mlx-server
python gui/app.py
```

### 7. Access the GUI

Open your browser and navigate to:

```
http://localhost:8080
```

---

## Testing the GUI

### Manual Testing Checklist

1. **Server Stopped State**:
   - [ ] Open `http://localhost:8080` (server not running)
   - [ ] See "STOPPED" status indicator
   - [ ] Click "Start Server" → should start MLX server
   - [ ] Status should change to "RUNNING" after refresh

2. **Server Running State**:
   - [ ] Start MLX server (via `just start` or another method)
   - [ ] Open `http://localhost:8080`
   - [ ] See "RUNNING" status indicator
   - [ ] See model information (if available)
   - [ ] Click "Stop Server" → should stop MLX server

3. **Error Handling**:
   - [ ] If `just` command fails, see error message
   - [ ] If MLX server is not reachable, see "STOPPED" status

---

## Development Workflow

### Making Changes

1. Edit files in `gui/` directory
2. Restart the Flask app (`Ctrl+C` then `python gui/app.py`)
3. Refresh browser to see changes

### Running Tests

```bash
# From project root
pytest gui/tests/
```

### Adding New Features

Follow the patterns in:
- [`specs/009-admin-gui-mvp/plan.md`](plan.md) - Implementation plan
- [`specs/009-admin-gui-mvp/data-model.md`](data-model.md) - Data models
- [`specs/009-admin-gui-mvp/contracts/`](contracts/) - Interface contracts

---

## Troubleshooting

### GUI won't start - Port 8080 in use
```bash
# Find process using port 8080
lsof -i :8080
# Kill if needed
kill -9 <PID>
```

### just command not found
```bash
# Install just
brew install just  # macOS
# or
cargo install just  # Rust-based installation
```

### MLX server health check fails
- Verify MLX server is running on port 8000
- Check `http://localhost:8000/health` in browser
- Review `just status` output

---

## Next Steps

After verifying the MVP works:
1. Review the [Implementation Plan](plan.md) for Phase 2 tasks
2. Run `/speckit.tasks` to generate task list
3. Implement remaining features (log viewing, better error handling, etc.)

---

## References

- Feature Spec: [specs/009-admin-gui-mvp/spec.md](spec.md)
- Implementation Plan: [specs/009-admin-gui-mvp/plan.md](plan.md)
- Research: [specs/009-admin-gui-mvp/research.md](research.md)
- Constitution: [.specify/memory/constitution.md](../../.specify/memory/constitution.md)
