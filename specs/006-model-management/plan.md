# Implementation Plan: Model Management

**Branch**: `006-model-management` | **Date**: 2026-05-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-model-management/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Implement model management infrastructure for the local MLX server, providing `just` recipes for listing available model profiles (`models-list`), selecting and activating model profiles (`model-use <profile>`), and validating model configurations. The system will maintain a registry of model profiles (Nemotron-120B-48GB, GPT-OSS-120B, Qwen3.5-122B) with path validation and disk space checks to ensure reliable local inference on Apple Silicon memory-constrained systems.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: mlx-lm, pyyaml (for profiles.yaml), psutil (for disk space checks)  
**Storage**: File-based configuration (profiles.yaml), state file (.active-model), file-based locking (flock)  
**Testing**: pytest with unit tests for validation logic and integration tests for just recipes  
**Target Platform**: macOS (Apple Silicon) - local inference infrastructure
**Project Type**: CLI/infrastructure tool (just recipes + Python scripts)  
**Performance Goals**: List models < 2 seconds, switch profiles < 5 seconds (from spec success criteria)  
**Constraints**: Memory-constrained environment for 120B+ models, file-based state management, concurrent access protection via flock  
**Scale/Scope**: 3 target model profiles initially, extensible configuration through profiles.yaml

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Infrastructure-Only Scope | ✅ PASS | Feature adds model management infrastructure only, no product/web-stack code |
| II. Local Serving Reliability | ✅ PASS | Improves model selection and validation before server startup, enhancing reliability |
| III. Quantization and Memory First | ✅ PASS | Focuses on 120B+ model profiles with memory requirements tracking for Apple Silicon |
| IV. Just Command Bridge | ✅ PASS | Implements `just` recipes (models-list, model-use) as primary interface |
| V. Reversible, Testable Changes | ✅ PASS | File-based configuration with minimal, auditable scripts and validation tests |

**GATE RESULT**: ✅ ALL GATES PASSED - Proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/006-model-management/
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
├── model-management.py      # Model profile registry, validation, and state management
└── wrapper-config/
    ├── profiles.yaml        # Model profile definitions (Nemotron, GPT-OSS, Qwen)
    └── presets.yaml        # Existing preset configurations (reused)

tests/
├── test_model_management.py # Unit tests for model validation and registry
└── test_server_lifecycle.py # Existing lifecycle tests (update for model integration)

justfile                     # Updated with models-list, model-use recipes
```

**Structure Decision**: Single project structure with scripts directory for Python modules and justfile for operational recipes. Model profiles stored in existing wrapper-config directory. Tests co-located with existing test files.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - all gates passed.

## Phase 0: Research

### Research Findings

See [research.md](research.md) for detailed research on:
- Model profile configuration best practices for MLX
- File-based state management patterns for CLI tools
- Disk space validation techniques on macOS
- Concurrent access patterns using flock

## Phase 1: Design & Contracts

### Data Model

See [data-model.md](data-model.md) for:
- ModelProfile entity definition
- ModelRegistry structure
- ValidationResult schema
- State file format

### Interface Contracts

See [contracts/](contracts/) for:
- `just models-list` command interface
- `just model-use <profile>` command interface
- Model validation API contract

### Quickstart

See [quickstart.md](quickstart.md) for:
- Setting up model profiles
- Using model management commands
- Validation and troubleshooting

## Constitution Check (Post-Design)

*Re-evaluation after Phase 1 design completion*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Infrastructure-Only Scope | ✅ PASS | No scope creep - pure infrastructure code |
| II. Local Serving Reliability | ✅ PASS | Validation prevents bad model startups |
| III. Quantization and Memory First | ✅ PASS | Profiles include quantization config and memory estimates |
| IV. Just Command Bridge | ✅ PASS | All operations exposed via just recipes |
| V. Reversible, Testable Changes | ✅ PASS | Configuration-based with comprehensive tests |

**FINAL GATE RESULT**: ✅ ALL GATES PASSED - Ready for Phase 2 (tasks generation)
