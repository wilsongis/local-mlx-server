# Implementation Plan: MLX Server Wrapper

**Branch**: `004-mlx-server-wrapper` | **Date**: 2026-05-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/004-mlx-server-wrapper/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Create an MLX server wrapper that provides a CLI interface (`start`, `stop`, `status`, `health` subcommands) for managing `mlx_lm.server` instances with health monitoring, model profile selection supporting per-path hybrid quantization, and startup argument presets optimized for 120B+ model serving on Apple Silicon memory-constrained systems.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: mlx-lm, PyYAML, click (for CLI), psutil (for memory checks)
**Storage**: YAML configuration files (`scripts/wrapper-config/profiles.yaml`, `scripts/wrapper-config/presets.yaml`)
**Testing**: pytest (see `tests/` directory)
**Target Platform**: macOS/Apple Silicon (primary), Linux (secondary)
**Project Type**: CLI tool / server wrapper
**Performance Goals**: 120B+ model startup <5min, health checks <1s, shutdown <30s, memory usage <48GB for 120B+ models
**Constraints**: <48GB memory footprint for 120B+ models, OpenAI-compatible API via mlx_lm.server, graceful shutdown with active request handling
**Scale/Scope**: Single wrapper script (`scripts/mlx_wrapper.py`) with ~4 subcommands, 2 YAML config files, integration with `just` recipes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Infrastructure-Only Scope | ✅ PASS | Wrapper is infrastructure-only, no product/web UI code |
| II. Local Serving Reliability | ✅ PASS | Preserves mlx_lm.server OpenAI-compatible behavior, adds health checks |
| III. Quantization and Memory First | ✅ PASS | Implements per-path hybrid quantization, 120B+ memory optimization presets |
| IV. Just Command Bridge | ✅ PASS | Integrates with `just` recipes for start/stop/status/health operations |
| V. Reversible, Testable Changes | ✅ PASS | Minimal wrapper script, YAML configs, auditable operational scripts |

## Project Structure

### Documentation (this feature)

```text
specs/004-mlx-server-wrapper/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── cli-interface.md
│   └── health-endpoint.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
scripts/
├── mlx_wrapper.py                    # Main wrapper script with CLI subcommands
└── wrapper-config/
    ├── profiles.yaml                 # Model profile definitions
    └── presets.yaml                  # Startup presets for 120B+ models

tests/
└── test_mlx_wrapper.py              # Wrapper script tests

justfile                             # Operational recipes (mlx-start, mlx-stop, etc.)
```

**Structure Decision**: Single CLI wrapper script (`scripts/mlx_wrapper.py`) with YAML configuration files in `scripts/wrapper-config/`. This is infrastructure-only code following Constitution Principle I. All operational workflows exposed via `just` recipes per Principle IV.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
