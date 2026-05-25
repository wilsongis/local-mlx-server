"""
Data models for the Admin GUI MVP.

Implements the entities defined in data-model.md:
- ServerStatus: Current MLX server state
- ModelInfo: Model being served
- LogEntry: Server log line
- ServerAction: Control action (start/stop)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ModelInfo:
    """Represents the model currently being served by the MLX server."""

    name: Optional[str] = None
    quantization_config: Optional[str] = None
    path: Optional[str] = None


@dataclass
class LogEntry:
    """Represents a single line of server log output."""

    message: str
    level: str = "info"
    source: str = "unknown"
    timestamp: Optional[datetime] = None


@dataclass
class ServerAction:
    """Represents a control action performed via the GUI."""

    action: str  # "start" or "stop"
    timestamp: datetime
    success: bool
    message: Optional[str] = None


@dataclass
class ServerStatus:
    """Represents the current state of the MLX server."""

    status: str  # "running", "stopped", or "unknown"
    timestamp: datetime
    health_data: Optional[dict] = None
    error: Optional[str] = None

    @property
    def model_info(self) -> Optional[ModelInfo]:
        """Extract ModelInfo from health data when available."""
        if not self.health_data:
            return None
        model_name = self.health_data.get("model")
        quantization = self.health_data.get("quantization")
        if model_name:
            return ModelInfo(name=model_name, quantization_config=quantization)
        return None
