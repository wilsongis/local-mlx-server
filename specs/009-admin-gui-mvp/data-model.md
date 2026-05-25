# Data Model: Admin GUI MVP

**Feature**: Admin GUI MVP (009-admin-gui-mvp)
**Date**: 2026-05-24
**Status**: Complete

---

## Entities

### 1. ServerStatus

Represents the current state of the MLX server.

**Attributes**:
| Attribute | Type | Description |
|-----------|------|-------------|
| `status` | `str` | Current state: `"running"`, `"stopped"`, or `"unknown"` |
| `timestamp` | `datetime` | Timestamp of last status check (ISO 8601 format) |
| `health_data` | `dict \| None` | Response from health endpoint when running (contains model info, etc.) |
| `error` | `str \| None` | Error message if health check failed |

**State Transitions**:
```
[unknown] -- health check success --> [running]
[unknown] -- health check fail --> [stopped]
[running] -- health check fail --> [stopped]
[stopped] -- health check success --> [running]
```

**Validation Rules**:
- `status` must be one of: `"running"`, `"stopped"`, `"unknown"`
- `timestamp` should be within last 10 seconds to be considered "current"
- `health_data` should contain at minimum `{"status": "ok"}` when server is running

---

### 2. ModelInfo

Represents the model currently being served by the MLX server.

**Attributes**:
| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str \| None` | Model name (e.g., `"llama-3-120b-4bit"`) |
| `quantization_config` | `str \| None` | Quantization configuration (e.g., `"4bit"`, `"hybrid"`) |
| `path` | `str \| None` | Filesystem path to model files (if available) |

**Validation Rules**:
- When `ServerStatus.status == "running"`, `name` should not be `None`
- `quantization_config` should match known patterns: `"4bit"`, `"8bit"`, `"hybrid"`, etc.

**Source**:
- Primary: Parsed from `/health` endpoint response
- Fallback: Read from `.active-model` file in project root

---

### 3. LogEntry

Represents a single line of server log output.

**Attributes**:
| Attribute | Type | Description |
|-----------|------|-------------|
| `timestamp` | `datetime \| None` | When the log entry was created (may be parsed from log line) |
| `message` | `str` | The log message content |
| `level` | `str` | Log level: `"info"`, `"warning"`, `"error"`, `"debug"` (default: `"info"`) |
| `source` | `str` | Where the log came from: `"stdout"`, `"stderr"`, `"file"` |

**Validation Rules**:
- `message` is required (non-empty)
- `level` should be normalized to lowercase
- For MVP: only last N entries are kept (e.g., 100 lines)

---

### 4. ServerAction

Represents a control action performed via the GUI (start/stop).

**Attributes**:
| Attribute | Type | Description |
|-----------|------|-------------|
| `action` | `str` | The action performed: `"start"`, `"stop"` |
| `timestamp` | `datetime` | When the action was initiated |
| `success` | `bool` | Whether the action succeeded |
| `message` | `str \| None` | Output or error message from the `just` command |

**Validation Rules**:
- `action` must be one of: `"start"`, `"stop"`
- `success` is required
- `message` captures stdout/stderr from `just` command

---

## Relationships

```
ServerStatus (1) ----has model----> (0..1) ModelInfo
ServerStatus (1) ----generates----> (0..*) LogEntry
ServerAction (1) ----targets----> (1) ServerStatus
```

---

## Data Flow

### Status Polling Flow
```
[GUI] -- HTTP GET --> [MLX Server /health]
                  <-- {"status": "ok", "model": ...} --
[GUI] -- parse response --> [ServerStatus]
[GUI] -- extract model --> [ModelInfo]
```

### Server Control Flow
```
[User] -- clicks "Start" --> [GUI]
[GUI] -- subprocess --> [just start]
                     <-- (returncode, output) --
[GUI] -- parse result --> [ServerAction]
[GUI] -- update status --> [ServerStatus]
```

### Log Display Flow
```
[GUI] -- read logs --> [just logs OR log file]
                   <-- log lines --
[GUI] -- parse lines --> [LogEntry list]
[GUI] -- render --> [HTML template]
```

---

## Storage

For MVP, all data is **ephemeral** (in-memory only):

- `ServerStatus`: Stored in Flask app context, updated every 5 seconds via polling
- `ModelInfo`: Extracted from `ServerStatus.health_data` when available
- `LogEntry`: Last N lines stored in memory (no persistent storage)
- `ServerAction`: Logged for debugging, not persisted

**Future consideration**: If persistence is needed later, use SQLite or JSON file in `gui/data/` directory.

---

## Python Data Classes

Recommended implementation (in `gui/services/models.py`):

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class ModelInfo:
    name: Optional[str] = None
    quantization_config: Optional[str] = None
    path: Optional[str] = None

@dataclass
class LogEntry:
    message: str
    level: str = "info"
    source: str = "unknown"
    timestamp: Optional[datetime] = None

@dataclass
class ServerAction:
    action: str  # "start" or "stop"
    timestamp: datetime
    success: bool
    message: Optional[str] = None

@dataclass
class ServerStatus:
    status: str  # "running", "stopped", or "unknown"
    timestamp: datetime
    health_data: Optional[dict] = None
    error: Optional[str] = None
    
    @property
    def model_info(self) -> Optional[ModelInfo]:
        if not self.health_data:
            return None
        # Extract model info from health data
        model_name = self.health_data.get("model")
        return ModelInfo(name=model_name) if model_name else None
```
