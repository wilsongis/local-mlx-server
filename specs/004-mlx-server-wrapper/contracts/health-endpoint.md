# Health Endpoint Contract: MLX Server Wrapper

**Date**: 2026-05-11  
**Feature**: 004-mlx-server-wrapper  
**Status**: Complete

## Contract Format

The wrapper provides a health endpoint that aggregates mlx_lm.server status with system metrics.

---

## Endpoint: GET /health

**Full URL**: `http://{host}:{port}/health`

**Description**: Returns detailed health status of the MLX server including model loading state, memory usage, and system metrics.

---

## Request

**Method**: `GET`

**Headers**:
- `Accept: application/json` (optional, defaults to JSON)

**Query Parameters**:
- `wait` (boolean, optional): If `true`, wait for server to become ready (up to 5 minutes)
- `timeout` (integer, optional): Max seconds to wait if `wait=true` (default: 300)

**Example Request**:
```http
GET /health HTTP/1.1
Host: localhost:8080
Accept: application/json
```

---

## Response

### Success Response (200 OK)

**Content-Type**: `application/json`

**Body Schema**:
```json
{
  "status": "string (enum: initializing | ready | degraded | down)",
  "model": "string or null (model name if known)",
  "model_loaded": "boolean (true if model fully loaded)",
  "load_progress_pct": "integer (0-100, loading progress)",
  "memory_usage_gb": "float (current memory consumption)",
  "memory_limit_gb": "float (configured memory limit)",
  "uptime_seconds": "integer (server uptime, 0 if down)",
  "active_requests": "integer (current active inference requests)",
  "last_check_timestamp": "string (ISO 8601 datetime)",
  "system": {
    "cpu_percent": "float (0-100, CPU usage)",
    "memory_available_gb": "float (available system memory)",
    "disk_free_gb": "float (free disk space in model directory)"
  }
}
```

**Example Response** (ready):
```json
{
  "status": "ready",
  "model": "Nemotron-120B",
  "model_loaded": true,
  "load_progress_pct": 100,
  "memory_usage_gb": 45.2,
  "memory_limit_gb": 48,
  "uptime_seconds": 9240,
  "active_requests": 0,
  "last_check_timestamp": "2026-05-11T14:05:31Z",
  "system": {
    "cpu_percent": 12.5,
    "memory_available_gb": 2.8,
    "disk_free_gb": 120.5
  }
}
```

**Example Response** (initializing):
```json
{
  "status": "initializing",
  "model": "Nemotron-120B",
  "model_loaded": false,
  "load_progress_pct": 45,
  "memory_usage_gb": 28.3,
  "memory_limit_gb": 48,
  "uptime_seconds": 120,
  "active_requests": 0,
  "last_check_timestamp": "2026-05-11T14:02:31Z",
  "system": {
    "cpu_percent": 85.0,
    "memory_available_gb": 19.7,
    "disk_free_gb": 120.5
  }
}
```

---

### Error Responses

**503 Service Unavailable** (server down or not responding):
```json
{
  "status": "down",
  "model": null,
  "model_loaded": false,
  "load_progress_pct": 0,
  "memory_usage_gb": 0,
  "memory_limit_gb": 48,
  "uptime_seconds": 0,
  "active_requests": 0,
  "last_check_timestamp": "2026-05-11T14:05:31Z",
  "error": "Server not responding"
}
```

**500 Internal Server Error** (unexpected error):
```json
{
  "status": "degraded",
  "error": "Failed to query mlx_lm.server: Connection refused",
  "last_check_timestamp": "2026-05-11T14:05:31Z"
}
```

---

## Health Status Definitions

| Status | Description | Model Loaded | Accepts Requests |
|--------|-------------|--------------|------------------|
| `initializing` | Server starting, model loading | false (0-99%) | No |
| `ready` | Fully operational | true (100%) | Yes |
| `degraded` | Running with issues (high memory, errors) | true | Yes (with warnings) |
| `down` | Not running or not responding | false | No |

---

## Status Transitions

```
[startup] → initializing → ready
                                ↓
                         (issues) → degraded → ready (recovery)
                                ↓
                         (persistent errors) → down
                                ↑
                         (restart) ← down
```

---

## Integration with mlx_lm.server

The wrapper health endpoint:
1. Proxies to mlx_lm.server's `/v1/models` endpoint for base status
2. Adds wrapper-level metrics (memory, system stats)
3. Tracks model loading progress if not yet ready
4. Returns HTTP 200 for all statuses except `down` (returns 503)

**Note**: The `/health` endpoint is provided by the wrapper, not mlx_lm.server. If mlx_lm.server is running on port 8080, the wrapper can either:
- Run on a separate port (e.g., 8081) for health checks
- Proxy the `/health` path if mlx_lm.server doesn't use it
- Use the same port and intercept `/health` before passing to mlx_lm.server

**Recommended**: Run wrapper health endpoint on separate port (configurable, default: 8081) to avoid conflicts.

---

## Monitoring Integration

The health endpoint is designed for:
- **Load balancers**: Use `/health` for health checks (HTTP 200 = healthy)
- **Prometheus**: Scrape metrics (consider separate `/metrics` endpoint for detailed metrics)
- **Uptime monitoring**: Simple GET request to verify liveness
- **Wrapper CLI**: `mlx-wrapper health` command queries this endpoint

---

## Security Considerations

- No authentication required (health endpoint is read-only, informational)
- Does not expose sensitive data (no API keys, model paths, or internal config)
- Consider disabling in high-security environments via configuration
- Rate limit not required (localhost-only by default)
