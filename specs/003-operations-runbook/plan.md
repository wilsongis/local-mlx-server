# Implementation Plan: Operations Runbook

**Branch**: `003-operations-runbook` | **Date**: 2026-05-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-operations-runbook/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Update OPERATIONS.md to become a comprehensive operations runbook documenting all `just` recipes with examples and edge cases, a troubleshooting guide for common startup/memory issues, and a model profile selection decision tree for 48GB/64GB/96GB memory tiers. This is a documentation-only feature that consolidates operational knowledge for the local MLX server infrastructure.

## Technical Context

**Language/Version**: N/A (documentation feature)  
**Primary Dependencies**: N/A (documentation feature)  
**Storage**: Markdown files (OPERATIONS.md, specs/003-operations-runbook/)  
**Testing**: Documentation review and validation against justfile  
**Target Platform**: macOS/Apple Silicon (M-series)  
**Project Type**: Documentation/Infrastructure  
**Performance Goals**: N/A  
**Constraints**: Must follow AGENTS.md infrastructure-only scope; must use "just recipe" canonical terminology; must update existing OPERATIONS.md (not create new file)  
**Scale/Scope**: 3 user stories, ~10 just recipes to document, 8+ troubleshooting scenarios, 3-tier decision tree

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Infrastructure-Only Scope | ✅ PASS | Documentation is infrastructure-only, no product code |
| II. Local Serving Reliability | ✅ PASS | Improves operational reliability through better documentation |
| III. Quantization and Memory First | ✅ PASS | Documents memory profiles and quantization configurations |
| IV. Just Command Bridge | ✅ PASS | Primary focus is documenting `just` recipes per AGENTS.md |
| V. Reversible, Testable Changes | ✅ PASS | Documentation updates are reversible and testable via review |

**Gate Result**: ✅ ALL GATES PASSED

## Project Structure

### Documentation (this feature)

```text
specs/003-operations-runbook/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── checklists/
│   └── requirements.md  # Feature requirements checklist
└── contracts/           # Phase 1 output (if applicable)
```

### Source Code (repository root)

```text
OPERATIONS.md            # Primary deliverable - updated runbook
justfile                 # Reference for just recipe documentation
```

**Structure Decision**: Documentation-only feature updating existing OPERATIONS.md and referencing justfile. No new source code directories required.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected - all gates passed.

## Phase 0: Research

See [research.md](research.md) for detailed findings.

**Key Research Topics**:
- Current justfile recipe inventory and syntax patterns
- Common MLX server startup failure modes on Apple Silicon
- Memory tier performance characteristics for 120B+ models
- Troubleshooting best practices for OOM and port conflict scenarios

## Phase 1: Design

See [data-model.md](data-model.md) for entity definitions and [quickstart.md](quickstart.md) for operator guide.

**Design Decisions**:
- Update existing OPERATIONS.md (consolidation, not replacement)
- Use "just recipe" canonical terminology throughout
- Structure: Recipe Reference → Troubleshooting → Decision Tree → Developer Guidelines
- Include quantifiable metrics per memory tier (tok/s, context length, memory used)
