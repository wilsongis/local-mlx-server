# Contract: HTTP Endpoints

**Feature**: Admin GUI MVP (009-admin-gui-mvp)
**Date**: 2026-05-24
**Status**: Complete

---

## Overview

This contract defines the HTTP endpoints exposed by the Admin GUI Flask application running on `localhost:8080`.

---

## Endpoints

### 1. GET /

**Description**: Main dashboard page displaying server status, model info, and controls.

**Request**:
- Method: `GET`
- Auth: None (localhost-only MVP)
- Query params: None

**Response**: HTML (server-rendered template)
- Template: `index.html`
- Context data:
  - `server_status` (str): `"running"`, `"stopped"`, or `"unknown"`
  - `model_info` (dict|None): Model name and quantization config
  - `last_checked` (str): ISO 8601 timestamp
  - `error` (str|None): Error message if status check failed

**Example**:
```html
<!-- index.html -->
<h1>MLX Server Status: {{ server_status }}</h1>
{% if model_info %}
  <p>Model: {{ model_info.name }}</p>
  <p>Quantization: {{ model_info.quantization_config }}</p>
{% endif %}
<button onclick="startServer()">Start Server</button>
<button onclick="stopServer()">Stop Server</button>
```

---

### 2. GET /logs

**Description**: Log viewer page displaying recent server log output.

**Request**:
- Method: `GET`
- Auth: None
- Query params: None

**Response**: HTML (server-rendered template)
- Template: `logs.html`
- Context data:
  - `log_entries` (list): List of log entry dicts with `message`, `level`, `timestamp`
  - `server_running` (bool): Whether server is currently running

---

### 3. GET /api/status

**Description**: JSON endpoint for polling server status (used by JavaScript for auto-refresh).

**Request**:
- Method: `GET`
- Auth: None
- Query params: None

**Response**: JSON
```json
{
  "status": "running" | "stopped" | "unknown",
  "timestamp": "2026-05-24T20:49:00Z",
  "model": {
    "name": "llama-3-120b-4bit" | null,
    "quantization_config": "4bit" | null
  },
  "error": null | "error message"
}
```

**Status Codes**:
- `200 OK`: Status successfully retrieved (even if server is stopped)
- `500 Internal Server Error`: Unexpected error during status check

---

### 4. POST /api/start

**Description**: Trigger server start via `just start` command.

**Request**:
- Method: `POST`
- Auth: None
- Content-Type: `application/json` (optional for MVP)
- Body: None

**Response**: JSON
```json
{
  "success": true | false,
  "message": "Server started successfully" | "Error: ...",
  "timestamp": "2026-05-24T20:49:00Z"
}
```

**Side Effects**:
- Executes `just start` command via subprocess
- Updates server status after command completes

**Status Codes**:
- `200 OK`: Command executed (check `success` field for result)
- `500 Internal Server Error`: Failed to execute command

---

### 5. POST /api/stop

**Description**: Trigger server stop via `just stop` command.

**Request**:
- Method: `POST`
- Auth: None
- Content-Type: `application/json` (optional for MVP)
- Body: None

**Response**: JSON
```json
{
  "success": true | false,
  "message": "Server stopped successfully" | "Error: ...",
  "timestamp": "2026-05-24T20:49:00Z"
}
```

**Side Effects**:
- Executes `just stop` command via subprocess
- Updates server status after command completes

**Status Codes**:
- `200 OK`: Command executed (check `success` field for result)
- `500 Internal Server Error`: Failed to execute command

---

## JavaScript Polling Contract

The frontend JavaScript will poll `/api/status` every 5 seconds (per FR-005):

```javascript
// app.js - minimal polling
setInterval(async () => {
  const response = await fetch('/api/status');
  const data = await response.json();
  
  // Update status indicator
  document.getElementById('status').textContent = data.status;
  document.getElementById('status').className = data.status;
  
  // Update model info if available
  if (data.model && data.model.name) {
    document.getElementById('model-name').textContent = data.model.name;
  }
}, 5000); // 5 seconds
```

---

## Error Handling

All endpoints should handle errors gracefully:

- **Connection errors** (MLX server not reachable): Return `status: "stopped"` with `error` message
- **just command failures**: Return `success: false` with error message from command output
- **Unexpected exceptions**: Log server-side, return generic error message to client

---

## Testing Contract

pytest tests should verify:

```python
def test_index_page_loads(client):
    """GET / returns 200 and contains status indicator."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'MLX Server Status' in response.data

def test_api_status_returns_json(client):
    """GET /api/status returns valid JSON with status field."""
    response = client.get('/api/status')
    assert response.status_code == 200
    data = response.get_json()
    assert 'status' in data
    assert data['status'] in ['running', 'stopped', 'unknown']

def test_api_start_returns_json(client, mock_just_command):
    """POST /api/start returns success/failure JSON."""
    response = client.post('/api/start')
    assert response.status_code == 200
    data = response.get_json()
    assert 'success' in data
    assert 'message' in data
```
