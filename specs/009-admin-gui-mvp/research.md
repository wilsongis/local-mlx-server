# Research: Admin GUI MVP

**Feature**: Admin GUI MVP (009-admin-gui-mvp)
**Date**: 2026-05-24
**Status**: Complete

---

## Technology Decisions

### Decision 1: Web Framework - Flask

**Decision**: Use Flask as the backend web framework.

**Rationale**:
- Flask is already a dependency in `pyproject.toml` (line 9)
- Minimal setup required for server-rendered HTML templates
- Lightweight for MVP with minimal UI needs
- No need for async capabilities (FastAPI) since the GUI is local-only with minimal concurrent users
- Simpler than FastAPI for serving HTML templates directly

**Alternatives considered**:
- **FastAPI**: Rejected - async capabilities not needed for MVP; Flask already in dependencies
- **Django**: Rejected - too heavyweight for a simple admin GUI
- **Direct HTTP server (http.server)**: Rejected - no template rendering support

---

### Decision 2: Frontend Approach - Server-Rendered HTML with Minimal JavaScript

**Decision**: Use server-rendered HTML templates (Jinja2 via Flask) with minimal JavaScript only for status polling.

**Rationale**:
- Keeps the interface minimal as required by FR-008
- Server-rendered pages are simpler to build and maintain
- JavaScript only needed for periodic status polling (every 5 seconds per FR-005)
- Aligns with "Python backend + server-rendered HTML templates (minimal JS)" clarification from 2026-05-24

**Alternatives considered**:
- **Single Page Application (React/Vue)**: Rejected - too complex for MVP; violates minimal interface requirement
- **Full JavaScript polling**: Rejected - would require API endpoints; server-rendered pages are simpler

---

### Decision 3: `just` Command Integration

**Decision**: Execute `just` commands via Python's `subprocess` module.

**Rationale**:
- Direct subprocess calls are simple and effective for local command execution
- `just` is already the stable operational interface per Principle IV
- Commands to integrate: `just start`, `just stop`, `just status` (if available)
- Capture stdout/stderr for error reporting (FR-006)

**Implementation approach**:
```python
import subprocess

def run_just_command(command: str) -> tuple[bool, str]:
    """Run a just command and return (success, output)."""
    try:
        result = subprocess.run(
            ["just", command],
            capture_output=True,
            text=True,
            timeout=30
        )
        return (result.returncode == 0, result.stdout or result.stderr)
    except Exception as e:
        return (False, str(e))
```

**Alternatives considered**:
- **just API/library**: Does not exist - `just` is a command-line tool only
- **Direct shell commands**: Rejected - violates Principle IV (Just Command Bridge)

---

### Decision 4: Server Status Detection

**Decision**: Poll MLX server's HTTP health endpoint (`http://localhost:8000/health`) for status detection.

**Rationale**:
- Per clarification: "HTTP health endpoint polling (query MLX server's `/health`)"
- Default MLX server port is 8000 (per clarification)
- Health endpoint provides authoritative status (handles server started outside GUI)
- Periodic polling every 5 seconds meets FR-005 requirement

**Implementation approach**:
```python
import requests

def check_server_health(health_url: str = "http://localhost:8000/health") -> dict:
    """Check MLX server health endpoint."""
    try:
        response = requests.get(health_url, timeout=2)
        return {"running": True, "data": response.json()}
    except requests.RequestException:
        return {"running": False, "data": None}
```

**Alternatives considered**:
- **Process checking (psutil)**: Rejected - doesn't handle server started outside GUI
- **Port checking**: Rejected - port open doesn't guarantee server is healthy

---

### Decision 5: Model Information Display

**Decision**: Extract model info from MLX server's `/health` endpoint or `/v1/models` endpoint (OpenAI-compatible).

**Rationale**:
- FR-003 requires displaying model name and quantization configuration
- OpenAI-compatible endpoints typically expose model info
- If not available via API, fall back to reading `.active-model` file or `just status` output

**Implementation approach**:
- Primary: Parse health endpoint response for model info
- Secondary: Read `.active-model` file if server doesn't expose model info
- Display: Model name and quantization config (e.g., "llama-3-120b-4bit")

---

### Decision 6: Log Display

**Decision**: For MVP, display recent stdout/stderr from server process or read from log files if available.

**Rationale**:
- FR-007 mentions displaying recent server logs
- P3 priority (lower than status and model info)
- MVP scope: display last N lines (e.g., 50-100 lines)
- No persistent log storage required (per assumptions)

**Implementation approach**:
- Option A: Capture output from `just` commands if server is started via GUI
- Option B: Read from log files if server writes logs (check `just status` or server config)
- Option C (simplest): Display output from `just logs` command if available, else show "Log viewing not available"

---

## Integration Patterns

### Flask Route Structure

```
/               -> Main dashboard (status, controls, model info)
/logs           -> Log viewer page
/api/status     -> JSON status endpoint (for polling)
/api/start      -> Start server action
/api/stop       -> Stop server action
```

### Template Structure

```
templates/
├── base.html       # Common layout, navigation
├── index.html      # Dashboard with status, controls, model info
└── logs.html       # Log viewer
```

---

## Security Considerations

- GUI is localhost-only (per FR-007, assumptions)
- No authentication required for MVP (per assumptions)
- `just` commands run with same permissions as the GUI process
- No input validation needed for MVP (no user input beyond button clicks)

---

## Testing Strategy

- pytest for backend testing (per pyproject.toml)
- Mock `subprocess` calls for testing `just` command integration
- Mock `requests` calls for testing health endpoint polling
- Test Flask routes with test client

---

## Open Questions Resolved

| Question | Resolution |
|----------|-------------|
| What technology stack? | Python Flask + server-rendered HTML (clarified 2026-05-24) |
| What port for GUI? | 8080 (clarified 2026-05-24) |
| How to detect server status? | HTTP health endpoint polling (clarified 2026-05-24) |
| Where should GUI code reside? | `gui/` directory at repository root (clarified 2026-05-24) |
| What is default MLX server port? | 8000 (clarified 2026-05-24) |

---

## References

- Feature Spec: [specs/009-admin-gui-mvp/spec.md](specs/009-admin-gui-mvp/spec.md)
- Constitution: [.specify/memory/constitution.md](.specify/memory/constitution.md)
- AGENTS.md: [AGENTS.md](AGENTS.md) (web UI directory boundary rule)
- pyproject.toml: [pyproject.toml](pyproject.toml) (dependencies)
