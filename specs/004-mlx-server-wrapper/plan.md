# Implementation Plan: MLX Server Wrapper

**Branch**: `004-mlx-server-wrapper` | **Date**: 2026-05-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-mlx-server-wrapper/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Create an MLX server wrapper that provides a unified operational interface for mlx_lm.server with startup/shutdown workflows, health monitoring, model profile selection with per-path hybrid quantization support, and memory-optimized presets for 120B+ models on Apple Silicon. The wrapper integrates with `just` command recipes and uses YAML configuration for profile definitions.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: mlx-lm, PyYAML, Click (for CLI), psutil (for memory checks)  
**Storage**: YAML configuration files for model profiles and presets  
**Testing**: pytest (existing framework per tests/test_main.py)  
**Target Platform**: macOS/Apple Silicon (primary), Linux (secondary)  
**Project Type**: CLI tool / server wrapper  
**Performance Goals**: 120B+ model startup <5min on 48GB systems, health checks <1s, shutdown <30s  
**Constraints**: <48GB memory consumption for 120B+ models, OpenAI-compatible API preservation, Apple Silicon optimized  
**Scale/Scope**: Single wrapper script (~500 LOC), 3-5 model profiles, integration with existing justfile

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Infrastructure-Only Scope | ✅ PASS | Wrapper is pure infrastructure - no product/web-stack features |
| II. Local Serving Reliability | ✅ PASS | Preserves mlx_lm.server OpenAI-compatible behavior, adds health checks |
| III. Quantization and Memory First | ✅ PASS | Core focus on 120B+ models, hybrid quantization, KV cache compression |
| IV. Just Command Bridge | ✅ PASS | Integrates with just recipes (start, stop, status, health) |
| V. Reversible, Testable Changes | ✅ PASS | Minimal wrapper script, YAML configs, auditable operational scripts |

**Gate Result**: ALL PASSED - Proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/004-mlx-server-wrapper/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
scripts/
├── mlx-wrapper.py      # Main wrapper script with subcommands (start, stop, status, health)
└── wrapper-config/     # YAML configuration directory
    ├── profiles.yaml   # Model profile definitions with quantization settings
    └── presets.yaml    # 120B+ memory optimization presets

justfile                 # Updated with wrapper commands (start, stop, status, health)
```

**Structure Decision**: Single project structure with wrapper script in scripts/, YAML configs in scripts/wrapper-config/, and justfile integration at root. This maintains consistency with existing project layout.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations to justify - all constitution principles pass.
