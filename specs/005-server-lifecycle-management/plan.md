# Implementation Plan: Server Lifecycle Management

**Branch**: `005-server-lifecycle-management` | **Date**: 2026-05-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-server-lifecycle-management/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Implement server lifecycle management through `just` recipes (`server-start`, `server-stop`, `server-status`) with PID file management, port conflict resolution, and graceful shutdown with active request draining. This infrastructure-only feature ensures reliable MLX server operations on Apple Silicon systems with proper process tracking and resource cleanup.

## Technical Context

**Language/Version**: Python 3.11+ (for lifecycle management scripts), Bash (for just recipes)  
**Primary Dependencies**: psutil (for process management), requests (for health checks), mlx-lm (server runtime)  
**Storage**: PID file at `/tmp/mlx-server.pid` (configurable), log output to stdout/stderr  
**Testing**: pytest with process mocking (extend existing [`tests/test_main.py`](tests/test_main.py))  
**Target Platform**: macOS/Apple Silicon (primary), Linux (secondary)  
**Project Type**: Infrastructure scripts / just recipes  
**Performance Goals**: Server start <5s (excluding model load), status check <2s, graceful shutdown <30s  
**Constraints**: No product code, preserve OpenAI-compatible API, minimal server surface, reversible changes  
**Scale/Scope**: 3 just recipes, 1-2 Python helper scripts (~200 LOC), PID file management, port conflict detection

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Infrastructure-Only Scope | ✅ PASS | Pure operational recipes and scripts - no product/web-stack features |
| II. Local Serving Reliability | ✅ PASS | Improves server reliability with PID tracking, port conflict resolution, graceful shutdown |
| III. Quantization and Memory First | ✅ PASS | Graceful shutdown ensures proper memory release for 120B+ model serving |
| IV. Just Command Bridge | ✅ PASS | All operations exposed via `just server-start/stop/status` recipes |
| V. Reversible, Testable Changes | ✅ PASS | PID file management and just recipes are minimally invasive and testable |

**Gate Result**: ALL PASSED - Proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/005-server-lifecycle-management/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
├── checklists/          # Quality gates
│   └── requirements.md  # Completion checklist
└── contracts/           # Phase 1 output (/speckit.plan command)
    └── just-recipes.md  # just recipe interface contracts
```

### Source Code (repository root)

```text
scripts/
├── server-lifecycle.py  # Lifecycle management helper (PID, port, shutdown logic)
└── wrapper-config/      # (existing) YAML configuration directory

justfile                 # Updated with server-start, server-stop, server-status recipes
```

**Structure Decision**: Single helper script `server-lifecycle.py` in `scripts/` containing PID management, port conflict detection, and graceful shutdown logic. Just recipes call this helper. This maintains consistency with existing project layout and keeps infrastructure code centralized.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations to justify - all constitution principles pass.

## Phase 0: Research

*To be completed by `/speckit.plan` command - research existing PID management patterns, port conflict resolution techniques, and graceful shutdown strategies for Python/MLX processes.*

**Research Topics**:
1. PID file management best practices (atomic writes, stale detection)
2. Port conflict detection using `lsof`/`ss` vs `psutil` on macOS
3. Graceful shutdown signals (SIGTERM vs SIGINT) for mlx_lm.server
4. Active request draining patterns for Python HTTP servers
5. Existing just recipe patterns in current [`justfile`](justfile)

## Phase 1: Design

*To be completed by `/speckit.plan` command - design the just recipes, PID file format, port conflict resolution flow, and graceful shutdown sequence.*

**Design Artifacts**:
- `data-model.md` - PID file structure, status output format, configuration options
- `quickstart.md` - Quick reference for `just server-start/stop/status` usage
- `contracts/just-recipes.md` - Recipe interface contracts (args, env vars, exit codes)
- `research.md` - Phase 0 research findings

## Phase 2: Task Breakdown

*To be completed by `/speckit.tasks` command (NOT part of `/speckit.plan`)*

**Task Categories**:
1. **Infrastructure** - just recipe creation, PID file management
2. **Logic** - Port conflict detection, graceful shutdown implementation
3. **Testing** - Unit tests for lifecycle management, integration tests
4. **Documentation** - Update OPERATIONS.md, README.md with new recipes

## Dependencies

- **DEP-001**: [`justfile`](justfile) - Must be extended with lifecycle recipes
- **DEP-002**: [`scripts/mlx_wrapper.py`](scripts/mlx_wrapper.py) - May need integration hooks for graceful shutdown
- **DEP-003**: mlx_lm.server - Must support SIGTERM for graceful shutdown
- **DEP-004**: psutil Python package - For process and port management

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| mlx_lm.server doesn't handle SIGTERM gracefully | High - Force kill loses active requests | Test shutdown behavior, implement request draining wrapper if needed |
| PID file corruption or race conditions | Medium - False "already running" errors | Use atomic writes, validate PID file contents, check process alive |
| Port conflict with system processes | Low - Unlikely on default port 8080 | Skip system processes (PID < 100), require confirmation for non-user processes |
| macOS `lsof`/`ss` differences from Linux | Medium - Port detection fails on macOS | Use psutil (cross-platform) as primary, fallback to CLI tools |
