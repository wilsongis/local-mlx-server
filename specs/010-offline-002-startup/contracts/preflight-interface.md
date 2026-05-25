# Contract: Preflight Check Interface

**Feature**: 010-offline-002-startup | **Date**: 2026-05-24

## Overview

This contract defines the interfaces for the preflight check system, including the Python module API, health endpoint extensions, and `just` recipe specifications.

---

## 1. Python Module Interface

### Module: `scripts/preflight/checker.py`

**Purpose**: Main orchestrator for running all preflight checks.

**Public API**:

```python
class PreflightChecker:
    """Orchestrates preflight checks before server startup."""
    
    def __init__(self, model_path: str, config_path: Optional[str] = None):
        """
        Initialize preflight checker.
        
        Args:
            model_path: Path to the model directory
            config_path: Optional path to preflight-config.yaml
        """
        ...
    
    def run_all_checks(self) -> PreflightResult:
        """
        Run all preflight checks and return aggregated result.
        
        Returns:
            PreflightResult with all check results and decision
        
        Raises:
            PreflightError: If checks cannot be executed
        """
        ...
    
    def should_block_startup(self) -> bool:
        """Check if startup should be blocked due to critical failures."""
        ...
    
    def should_enter_degraded_mode(self) -> bool:
        """Check if system should enter degraded mode."""
        ...
```

### Module: `scripts/preflight/memory_check.py`

```python
def check_memory_budget(model_path: str) -> PreflightCheck:
    """
    Verify available GPU/memory meets model requirements.
    
    Returns:
        PreflightCheck with status (pass/fail/warning)
    
    Thresholds:
        - 120B+ model: 48GB (TurboQuant), 64GB (standard 4-bit)
        - From kv_cache_profiles.py: ModelSizeClass.SIZE_100B_PLUS.min_memory_gb
    """

def check_wired_limit() -> PreflightCheck:
    """
    Check wired memory usage is within acceptable limits.
    
    Returns:
        PreflightCheck with status
    
    Threshold:
        - Default: 12GB (configurable in preflight-config.yaml)
        - Uses ctypes to query IOKit for wired memory stats
    """
```

### Module: `scripts/preflight/disk_check.py`

```python
def check_disk_space(path: str = ".") -> PreflightCheck:
    """
    Verify sufficient disk space for model loading and operation.
    
    Args:
        path: Path to check (default: current directory)
    
    Returns:
        PreflightCheck with status
    
    Threshold:
        - Minimum: 50GB (configurable)
        - Accounts for model size + swap + temporary files
    """
```

### Module: `scripts/preflight/dependency_check.py`

```python
def check_mlx_integrity() -> PreflightCheck:
    """
    Verify MLX and mlx-lm are installed and compatible.
    
    Returns:
        PreflightCheck with version info
    
    Checks:
        - mlx-lm importable
        - Version >= 0.19.0 (minimum for TurboQuant)
        - mlx core dependency satisfied
    """

def check_turboquant_available() -> PreflightCheck:
    """
    Check if TurboQuant is available (non-critical).
    
    Returns:
        PreflightCheck with status
    """

def check_kv_cache_support() -> PreflightCheck:
    """
    Verify KV cache compression support (non-critical).
    
    Returns:
        PreflightCheck with status
    """
```

### Module: `scripts/preflight/profile_fallback.py`

```python
def determine_profile(model_path: str, explicit_profile: Optional[str] = None) -> str:
    """
    Determine quantization profile using fallback chain.
    
    Fallback chain (highest to lowest priority):
        1. explicit_profile (user-specified)
        2. Model-detected profile (from model_detector.py)
        3. Memory-based selection (48GB+ → TurboQuant, 64GB+ → standard)
        4. Safe default: "120b-balanced"
    
    Args:
        model_path: Path to model directory
        explicit_profile: Optional user-specified profile
    
    Returns:
        Profile name to use
    """
```

---

## 2. Health Endpoint Extension

### Endpoint: `GET /health/preflight`

**Extension to existing `mlx_lm.server` health endpoint.**

**Response Schema**:

```json
{
  "status": "healthy|degraded|blocked",
  "timestamp": "2026-05-24T18:00:00Z",
  "preflight": {
    "last_check": "2026-05-24T18:00:00Z",
    "overall_status": "ready|degraded|blocked",
    "execution_time_ms": 1250,
    "checks": [
      {
        "name": "memory_budget",
        "type": "critical",
        "status": "pass",
        "details": "64GB available, 48GB required for 120B+ model",
        "timestamp": "2026-05-24T18:00:00Z"
      },
      {
        "name": "turboquant",
        "type": "non_critical",
        "status": "fail",
        "details": "TurboQuant not installed",
        "error_code": "ERR-DEP-002"
      }
    ],
    "critical_failures": [],
    "non_critical_failures": ["turboquant"]
  },
  "degraded_mode": {
    "active": true,
    "disabled_features": ["turboquant", "kv_cache_compression"],
    "fallback_profile": "4bit-standard",
    "warnings": ["Running with reduced capabilities"]
  }
}
```

**Integration Point**: `scripts/mlx_server_wrapper.py` will patch the server app to add this endpoint (following pattern from lines 26-51 for KV cache patching).

---

## 3. Just Recipe Specification

### Recipe: `preflight`

**Purpose**: Manual preflight check execution without starting server.

**Definition** (to be added to `justfile`):

```makefile
# Run preflight checks without starting server
preflight MODEL_PATH="./models":
    @uv run python -m scripts.preflight.checker --model-path {{MODEL_PATH}}
```

**Expected Output**:
```
Running preflight checks for model: ./models
✓ [CRITICAL] Memory budget: 64GB available (48GB required)
✓ [CRITICAL] Wired limit: 8GB (limit: 12GB)
✓ [CRITICAL] Disk space: 100GB available (50GB required)
✓ [CRITICAL] MLX integrity: mlx-lm 0.19.0
✗ [NON-CRITICAL] TurboQuant: Not available
✗ [NON-CRITICAL] KV cache compression: Not available

Result: DEGRADED - Server can start with reduced capabilities
Disabled features: TurboQuant, KV cache compression
```

### Recipe: `run` (Modified)

**Existing recipe** (line 44-46 of `justfile`):
```makefile
run:
    @echo "Starting mlx_lm.server via uv..."
    uv run python -m mlx_lm.server --model {{MODEL_PATH}} --host {{HOST}} --port {{PORT}} --max-kv-size {{MAX_TOKENS}}
```

**Modified to include preflight**:
```makefile
run:
    @echo "Running preflight checks..."
    @uv run python -m scripts.preflight.checker --model-path {{MODEL_PATH}} --block-on-critical
    @echo "Starting mlx_lm.server via uv..."
    uv run python scripts/mlx_server_wrapper.py --model {{MODEL_PATH}} --host {{HOST}} --port {{PORT}}
```

---

## 4. Configuration File Interface

### File: `scripts/wrapper-config/preflight-config.yaml`

```yaml
# Preflight configuration for local MLX server
# Documentation: specs/010-offline-002-startup/

# Memory thresholds (in GB)
memory:
  critical_120b: 48      # Minimum for TurboQuant 120B+
  standard_120b: 64      # Minimum for standard 4-bit 120B
  warning_threshold: 56   # Warning below this
  wired_limit: 12         # Max wired memory (GB)

# Disk space (in GB)
disk:
  min_required: 50
  check_path: "."         # Path to check

# Dependency checks
dependencies:
  mlx_lm_min_version: "0.19.0"
  check_turboquant: true   # non-critical
  check_kv_cache: true     # non-critical

# Profile fallback chain (in priority order)
profile_fallback:
  - "user_specified"
  - "model_detected"
  - "memory_based"
  - "120b-balanced"        # Safe default

# Degraded mode configuration
degraded_mode:
  disabled_features:
    - "turboquant"
    - "kv_cache_compression"
    - "advanced_profiling"
  fallback_quantization: "4bit-standard"
```

---

## 5. Admin GUI Integration

### Service: `gui/services/status_monitor.py` (Extended)

**New method** to fetch preflight status:

```python
def get_preflight_status() -> Dict:
    """
    Fetch preflight status from health endpoint.
    
    Returns:
        Dict with preflight results and degraded mode status
    
    Endpoint:
        GET http://{HOST}:{PORT}/health/preflight
    """
    ...
```

### Template: `gui/templates/index.html` (Extended)

**New section** for degraded mode banner:

```html
{% if preflight.degraded_mode.active %}
<div class="alert alert-warning">
    <strong>Degraded Mode Active</strong>
    <p>Server running with reduced capabilities:</p>
    <ul>
        {% for feature in preflight.degraded_mode.disabled_features %}
        <li>{{ feature }} disabled</li>
        {% endfor %}
    </ul>
</div>
{% endif %}
```

---

## Contract Compliance

| Component | Interface Defined | Status |
|-----------|-------------------|--------|
| `scripts/preflight/checker.py` | Python class API | ✅ Defined |
| `scripts/preflight/memory_check.py` | Function signatures | ✅ Defined |
| `scripts/preflight/disk_check.py` | Function signatures | ✅ Defined |
| `scripts/preflight/dependency_check.py` | Function signatures | ✅ Defined |
| `scripts/preflight/profile_fallback.py` | Function signature | ✅ Defined |
| Health endpoint `/health/preflight` | JSON schema | ✅ Defined |
| `justfile` recipe `preflight` | Command spec | ✅ Defined |
| `preflight-config.yaml` | YAML schema | ✅ Defined |
| `gui/services/status_monitor.py` | Method extension | ✅ Defined |

---

## References

- Feature Spec: [`../spec.md`](../spec.md)
- Data Model: [`../data-model.md`](../data-model.md)
- Existing KV cache patching pattern: `scripts/mlx_server_wrapper.py` lines 26-51
- Existing health endpoint: `mlx_lm.server` (FastAPI-based)
- Constitution: [`.specify/memory/constitution.md`](../../.specify/memory/constitution.md)
