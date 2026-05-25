# Research: Startup Preflight and Degraded Mode

**Feature**: 010-offline-002-startup | **Date**: 2026-05-24

## Research Questions & Findings

### RQ-001: How to check Apple Silicon GPU memory and wired memory limits on macOS?

**Decision**: Use `psutil` with macOS-specific system calls via `ctypes` to `libSystem.dylib` for GPU/wired memory detection.

**Rationale**: 
- `psutil` already a project dependency (used in `scripts/server-lifecycle.py` lines 20-21)
- Native macOS APIs accessible via `ctypes` without additional dependencies
- `psutil.virtual_memory()` provides unified memory info; GPU memory on Apple Silicon shares unified memory
- Wired memory can be queried via `host_statistics64` from `libSystem.dylib`

**Alternatives considered**:
- `subprocess` calls to `vm_stat` or `sysctl` - rejected due to parsing overhead and fragility
- `objc` bridge for direct IOKit queries - rejected due to additional dependency requirement

**Implementation approach**:
```python
import ctypes
import ctypes.util

# Load system library for host statistics
libsystem = ctypes.CDLL(ctypes.util.find_library("System"))

# Use host_statistics64 for wired memory
# vm_statistics64 structure parsing for wired pages
```

**References**: 
- `scripts/server-lifecycle.py` already imports `psutil` (line 20)
- Apple Developer Documentation: `host_statistics64`, `vm_statistics64`

---

### RQ-002: What are the memory requirements for 120B+ models with TurboQuant?

**Decision**: 
- **Critical threshold**: 48GB unified memory for 120B+ models with TurboQuant hybrid quantization (3-bit attention, 2-bit experts)
- **Standard threshold**: 64GB unified memory for standard 4-bit quantization
- **Warning threshold**: 56GB (between critical and standard)

**Rationale**:
- From `docs/research/Nemotron 120B on a 48 GB MacBook...md`: 120B model with TurboQuant runs on 48GB
- From `scripts/quantization/kv_cache_profiles.py` lines 35-37: `SIZE_100B_PLUS.min_memory_gb = 48`
- Constitution Principle III emphasizes 120B+ serving viability on memory-constrained systems

**Validation method**:
```python
# From kv_cache_profiles.py
if total_memory_gb >= 48 and model_size_class == "100B+":
    return "turboquant"  # Use hybrid quantization
elif total_memory_gb >= 64:
    return "standard"    # Use 4-bit quantization
else:
    return "insufficient" # Block startup
```

---

### RQ-003: How to verify MLX and dependency integrity?

**Decision**: Check importability, version compatibility, and model path accessibility.

**Rationale**:
- `mlx_lm.__version__` provides version info (used in `justfile` line 85)
- Model path must exist and contain valid model files (`config.json`, `*.safetensors`)
- Dependency chain: `mlx-lm` → `mlx` → `turboquant` (optional)

**Implementation**:
```python
import importlib.metadata

# Version check
mlx_version = importlib.metadata.version("mlx-lm")
# Parse version, check >= minimum required (e.g., 0.19.0)

# Model path validation
model_path = Path(model_path_str)
assert (model_path / "config.json").exists()
assert any(model_path.glob("*.safetensors"))
```

**References**:
- `justfile` line 85: `uv run python -c "import mlx_lm; print(f'mlx_lm version: {mlx_lm.__version__}')"`
- `scripts/quantization/model_detector.py` for model path validation patterns

---

### RQ-004: How to implement deterministic profile fallback?

**Decision**: Implement a priority-based fallback chain: User-specified → Model-detected → Memory-based → Safe default.

**Rationale**:
- User may specify profile via `--profile` flag or environment variable
- Model detection (`scripts/quantization/model_detector.py`) determines optimal profile
- Memory availability dictates feasible quantization strategy
- Safe default (e.g., `120b-balanced`) ensures startup without user input

**Fallback chain**:
1. Explicit profile argument (highest priority)
2. Model architecture detection result
3. Memory-based selection (48GB+ → TurboQuant, 64GB+ → standard 4-bit)
4. Safe default: `120b-balanced` preset from `scripts/wrapper-config/presets.yaml`

**Implementation**:
```python
def determine_profile(model_path, explicit_profile=None):
    if explicit_profile:
        return explicit_profile  # User choice
    
    detector = ModelDetector(model_path)
    arch = detector.detect()
    
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    if arch.size_class == "100B+" and memory_gb >= 48:
        return "tq3a-tq2e-g32"  # TurboQuant hybrid
    elif memory_gb >= 64:
        return "4bit-standard"
    else:
        return "120b-balanced"  # Safe default
```

**References**:
- `scripts/wrapper-config/presets.yaml` for preset definitions
- `scripts/quantization/quantization_manager.py` lines 63-80 for profile loading

---

### RQ-005: How to extend `mlx_lm.server` health endpoint for preflight/degraded status?

**Decision**: Add custom `/health` endpoint wrapper that augments the default `mlx_lm.server` health response with preflight results and degraded mode status.

**Rationale**:
- `mlx_lm.server` provides base health endpoint (FastAPI-based)
- Can subclass or wrap the FastAPI app to add custom routes
- Constitution Principle II requires preserving OpenAI-compatible endpoint behavior
- Non-invasive approach: add middleware or startup event hook

**Implementation approach**:
```python
from mlx_lm.server import create_app

app = create_app(model_path)

# Add custom health endpoint
@app.get("/health/preflight")
async def preflight_status():
    return {
        "status": "degraded" if degraded_mode else "healthy",
        "preflight_results": preflight_results,
        "degraded_features": disabled_features if degraded_mode else []
    }
```

**Alternative**: Extend `scripts/mlx_server_wrapper.py` to patch the server app at startup (following existing KV cache patching pattern from lines 26-51).

**References**:
- `scripts/mlx_server_wrapper.py` lines 26-51: Existing server patching pattern
- `scripts/quantization/server_integration.py`: `patch_mlx_server_for_kv_compression` pattern

---

### RQ-006: How should degraded mode disable features?

**Decision**: Feature flags in configuration, disabled features list in health endpoint, and graceful degradation in `mlx_server_wrapper.py`.

**Rationale**:
- FR-007 specifies disabling: TurboQuant hybrid quantization, KV cache compression, advanced profiling
- Feature flags allow runtime checks without code branching
- Health endpoint communicates disabled features to Admin GUI

**Implementation**:
```python
DEGRADED_CONFIG = {
    "disable_turboquant": True,
    "disable_kv_cache_compression": True,
    "disable_profiling": True,
    "fallback_quantization": "4bit",  # Standard quantization
}

# In mlx_server_wrapper.py
if degraded_mode:
    os.environ["TURBOQUANT_ENABLED"] = "false"
    os.environ["KV_CACHE_ENABLED"] = "false"
```

**References**:
- FR-007 in `spec.md`: Lists features to disable in degraded mode
- `scripts/mlx_wrapper.py` or `scripts/mlx_server_wrapper.py` for server startup logic

---

## Summary of Decisions

| Decision | Rationale | Alternatives Rejected |
|----------|-----------|------------------------|
| Use `psutil` + `ctypes` for memory checks | Already a dependency, no new deps | `vm_stat` parsing, IOKit via `objc` |
| 48GB/64GB memory thresholds | Research docs + existing code | Custom user config (too complex) |
| Priority-based profile fallback | Deterministic, user-respectful | Random selection, always-default |
| Health endpoint extension via wrapper | Non-invasive, follows existing patterns | Fork `mlx_lm.server`, monkey-patching |
| Feature flags for degraded mode | Clean, testable, reversible | Code branching, config file editing |

## Open Questions

None. All NEEDS CLARIFICATION items resolved through research.
