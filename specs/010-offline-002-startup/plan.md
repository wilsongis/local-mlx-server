# Implementation Plan: Startup Preflight and Degraded Mode for Apple Silicon Local Serving

**Branch**: `010-offline-002-startup` | **Date**: 2026-05-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/010-offline-002-startup/spec.md`

## Summary

Implement a comprehensive preflight check system that validates system readiness before starting the MLX server on Apple Silicon hardware. The system will check memory budget (GPU/wired memory), disk space, dependency integrity, and provide deterministic profile fallback. Critical check failures block startup; non-critical failures trigger degraded mode with reduced capabilities.

## Technical Context

**Language/Version**: Python 3.11+ (managed via `uv`)

**Primary Dependencies**: 
- `mlx-lm` (core serving runtime)
- `psutil` (system resource monitoring - already in use by `server-lifecycle.py`)
- `yaml` (profile configuration - already used by quantization modules)
- `requests` (health endpoint checks - already in use)

**Storage**: File-based configuration in `scripts/wrapper-config/`, PID file at `/tmp/mlx-server.pid`

**Testing**: `pytest` (existing test framework with tests in `/tests/`)

**Target Platform**: macOS (Apple Silicon M1/M2/M3) with unified memory architecture

**Project Type**: Infrastructure / CLI tool with server wrapper

**Performance Goals**: 
- Preflight checks complete within 5 seconds (SC-002)
- Server startup blocked within 1 second of critical failure (SC-003)
- Degraded mode activates within 2 seconds of non-critical failure (SC-004)

**Constraints**:
- Must preserve OpenAI-compatible API via `mlx_lm.server` (Constitution II)
- Must use `just` recipes for operational workflows (Constitution IV)
- Memory-constrained environment (48-64GB for 120B+ models)
- Reversible, testable changes (Constitution V)

**Scale/Scope**: 
- 5 preflight check categories (memory, wired-limit, disk, dependencies, profile fallback)
- Integration with existing `scripts/server-lifecycle.py` and `scripts/mlx_server_wrapper.py`
- Health endpoint extension for preflight/degraded status
- Admin GUI notification via existing `gui/services/` layer

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Infrastructure-Only Scope | ✅ PASS | Changes limited to server startup infrastructure, no product web-stack features |
| II. Local Serving Reliability | ✅ PASS | Improves startup reliability through preflight validation |
| III. Quantization and Memory First | ✅ PASS | Memory budget and profile fallback directly support 120B+ model serving |
| IV. Just Command Bridge | ✅ PASS | New `just` recipe `preflight` will be added for manual checks |
| V. Reversible, Testable Changes | ✅ PASS | Each check is independently testable; changes are minimal and auditable |

**Verdict**: ✅ ALL GATES PASSED

## Project Structure

### Documentation (this feature)

```text
specs/010-offline-002-startup/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── preflight-interface.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
scripts/
├── server-lifecycle.py          # EXTEND: Add preflight check integration
├── mlx_server_wrapper.py       # EXTEND: Call preflight before server start
├── preflight/                  # NEW: Preflight check modules
│   ├── __init__.py
│   ├── checker.py              # Main preflight orchestrator
│   ├── memory_check.py         # Memory budget & wired-limit checks
│   ├── disk_check.py           # Disk space validation
│   ├── dependency_check.py     # Dependency integrity verification
│   └── profile_fallback.py    # Deterministic profile fallback
└── wrapper-config/
    └── preflight-config.yaml   # NEW: Preflight configuration

gui/
└── services/
    └── status_monitor.py       # EXTEND: Add preflight/degraded status

justfile                         # EXTEND: Add preflight recipe
```

**Structure Decision**: New `scripts/preflight/` package encapsulates all preflight logic, keeping `server-lifecycle.py` and `mlx_server_wrapper.py` changes minimal. Configuration in `wrapper-config/` follows existing pattern.

## Complexity Tracking

> No constitution violations detected. All changes align with infrastructure-only scope and reversible change principles.

## Phase 0: Research Notes

See [`research.md`](research.md) for detailed findings on:
- Apple Silicon memory management (wired vs. GPU memory)
- `psutil` capabilities for memory/disk checks on macOS
- MLX version compatibility detection
- Deterministic profile selection strategies
- Health endpoint extension patterns for `mlx_lm.server`

## Phase 1: Design Notes

See [`data-model.md`](data-model.md) for entity definitions:
- `PreflightCheck`: Individual check result
- `PreflightResult`: Aggregated check results with degradation decision
- `DegradedModeConfig`: Fallback configuration for degraded operation

See [`contracts/preflight-interface.md`](contracts/preflight-interface.md) for:
- Python module interface (`scripts/preflight/checker.py`)
- Health endpoint contract extensions
- `just` recipe specification

See [`quickstart.md`](quickstart.md) for usage examples.
