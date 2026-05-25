---
description: "Task list for Startup Preflight and Degraded Mode feature"
---

# Tasks: Startup Preflight and Degraded Mode for Apple Silicon Local Serving

**Input**: Design documents from `/specs/010-offline-002-startup/`

**Prerequisites**: plan.md, spec.md, data-model.md, contracts/preflight-interface.md, quickstart.md

**Tests**: Tests are NOT included (not explicitly requested in feature specification)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for preflight feature

- [x] T001 Create `scripts/preflight/` package directory with `__init__.py` in `scripts/preflight/__init__.py`
- [x] T002 [P] Create `scripts/wrapper-config/preflight-config.yaml` with default thresholds (memory: 48GB, wired-limit: 12GB, disk: 50GB)
- [x] T003 [P] Add `psutil` dependency to `pyproject.toml` if not already present (verify in `pyproject.toml`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Implement `PreflightCheck` dataclass in `scripts/preflight/checker.py` (fields: name, check_type, status, details, timestamp, error_code)
- [x] T005 Implement `PreflightResult` dataclass in `scripts/preflight/checker.py` (fields: checks, overall_status, critical_failures, non_critical_failures, degraded_mode, block_startup, execution_time_ms)
- [x] T006 Implement `DegradedModeConfig` dataclass in `scripts/preflight/checker.py` (fields: enabled, disabled_features, fallback_quantization, fallback_profile, warnings)
- [x] T007 [P] Implement memory budget check in `scripts/preflight/memory_check.py` (function: `check_memory_budget(model_path: str) -> PreflightCheck`)
- [x] T008 [P] Implement wired memory limit check in `scripts/preflight/memory_check.py` (function: `check_wired_limit() -> PreflightCheck`)
- [x] T009 [P] Implement disk space check in `scripts/preflight/disk_check.py` (function: `check_disk_space(path: str = ".") -> PreflightCheck`)
- [x] T010 [P] Implement dependency check in `scripts/preflight/dependency_check.py` (function: `check_dependencies() -> PreflightCheck`)
- [x] T011 [P] Implement profile fallback in `scripts/preflight/profile_fallback.py` (function: `determine_fallback_profile(model_path: str) -> str`)
- [x] T012 Implement `PreflightChecker` class orchestrator in `scripts/preflight/checker.py` (methods: `run_all_checks() -> PreflightResult`, `should_block_startup() -> bool`, `should_enter_degraded_mode() -> bool`)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Startup Preflight Validation (Priority: P1) 🎯 MVP

**Goal**: Automatically run preflight checks before starting the MLX server, blocking startup if critical checks fail.

**Independent Test**: Can be fully tested by triggering a server start attempt and verifying preflight checks execute and block startup if critical checks fail.

### Implementation for User Story 1

- [x] T013 [US1] Integrate `PreflightChecker` into `scripts/server-lifecycle.py` - call `run_all_checks()` before server start in `start_server()` function
- [x] T014 [US1] Add startup blocking logic in `scripts/server-lifecycle.py` - if `should_block_startup()` returns True, abort startup and return error with check details
- [x] T015 [US1] Integrate `PreflightChecker` into `scripts/mlx_server_wrapper.py` - call preflight before `mlx_lm.server` startup in wrapper main flow
- [x] T016 [US1] Add `just preflight` recipe in `justfile` - runs preflight checks without starting server, accepts optional `MODEL_PATH` argument
- [x] T017 [US1] Add `just preflight-offline` recipe in `justfile` - runs preflight checks using cached/offline model detection without network calls
- [x] T018 [US1] Add logging for preflight results in `scripts/preflight/checker.py` - log all check results with timestamps to server logs (FR-008)
- [x] T019 [US1] Add clear error messaging in `scripts/server-lifecycle.py` - format failed checks into user-readable error output with suggested fixes

**Checkpoint**: At this point, User Story 1 should be fully functional - server startup runs preflight checks and blocks on critical failures.

---

## Phase 4: User Story 2 - Degraded Mode Operation (Priority: P2)

**Goal**: If non-critical preflight checks fail, enter degraded mode with reduced capabilities instead of blocking startup.

**Independent Test**: Can be fully tested by simulating a failed non-critical check (e.g., missing TurboQuant) and verifying the server starts in degraded mode.

### Implementation for User Story 2

- [x] T020 [US2] Implement degraded mode activation in `scripts/preflight/checker.py` - when `should_enter_degraded_mode()` returns True, populate `DegradedModeConfig` with disabled features (TurboQuant, KV cache compression, advanced profiling)
- [x] T021 [US2] Add fallback quantization selection in `scripts/preflight/profile_fallback.py` - set `fallback_quantization` to "4bit-standard" and `fallback_profile` to appropriate preset from `scripts/wrapper-config/presets.yaml`
- [x] T022 [US2] Integrate degraded mode into `scripts/server-lifecycle.py` - if `should_enter_degraded_mode()` is True, start server with degraded config instead of blocking
- [x] T023 [US2] Modify `scripts/mlx_server_wrapper.py` - pass degraded mode flags to disable TurboQuant and KV cache compression when in degraded mode
- [x] T024 [US2] Add degraded mode logging in `scripts/server-lifecycle.py` - log degraded mode activation with list of disabled features and fallback settings
- [x] T025 [US2] Update `just preflight` recipe output in `justfile` - display degraded mode status and disabled features when non-critical checks fail

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - critical failures block startup, non-critical failures trigger degraded mode.

---

## Phase 5: User Story 3 - Preflight and Degraded Mode Notification (Priority: P3)

**Goal**: Users receive clear, actionable feedback about preflight check results and degraded mode status via server logs, health endpoints, and Admin GUI.

**Independent Test**: Can be fully tested by checking log output, health endpoint responses, and Admin GUI status indicators after preflight checks or degraded mode activation.

### Implementation for User Story 3

- [x] T026 [US3] Extend health endpoint in `scripts/server-lifecycle.py` - add `/health/preflight` endpoint returning `PreflightResult` as JSON (FR-009)
- [x] T027 [US3] Add preflight status to main health endpoint in `scripts/server-lifecycle.py` - include `preflight.overall_status` and `degraded_mode.active` in `/health` response (FR-009, SC-007)
- [x] T028 [US3] Update `gui/services/status_monitor.py` - add `get_preflight_status()` method that queries `/health/preflight` endpoint
- [x] T029 [US3] Update `gui/services/status_monitor.py` - add `get_degraded_mode_status()` method returning disabled features and fallback config
- [x] T030 [US3] Update `gui/templates/index.html` - add degraded mode warning banner displaying when system is in degraded mode (FR-010)
- [x] T031 [US3] Update `gui/static/style.css` - add styles for degraded mode warning banner (red/orange alert styling)
- [x] T032 [US3] Update `gui/static/app.js` - add polling logic to check degraded mode status and display warning banner dynamically

**Checkpoint**: All user stories should now be independently functional - preflight checks, degraded mode, and notifications all working.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T033 [P] Update `README.md` - document new preflight feature, `just preflight` and `just preflight-offline` commands
- [x] T034 [P] Update `OPERATIONS.md` - add preflight check procedures, degraded mode troubleshooting, and health endpoint documentation
- [x] T035 Validate `scripts/wrapper-config/preflight-config.yaml` - ensure all thresholds match FR-002, FR-003, FR-004 requirements
- [x] T036 Performance validation - verify preflight checks complete within 5 seconds (SC-002) using `time` command
- [x] T037 [P] Add error handling edge cases in `scripts/preflight/` - handle missing `psutil`, invalid model paths, corrupted config files
- [x] T038 Integration test - run `just preflight` with various failure scenarios and verify correct behavior (blocked vs degraded vs ready)
- [x] T039 Run `just preflight-offline` validation - verify offline mode works without network calls
- [x] T040 Update `RUN-SHEET.md` - add preflight and degraded mode entries to operational run sheet

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Models (dataclasses) before services (orchestrators)
- Services before integration points
- Core implementation before logging/notification
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Different user stories can be worked on in parallel by different team members
- Polish tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all parallel tasks for User Story 1 together:
Task: "Integrate PreflightChecker into scripts/server-lifecycle.py"
Task: "Integrate PreflightChecker into scripts/mlx_server_wrapper.py"
Task: "Add just preflight recipe in justfile"
Task: "Add logging for preflight results in scripts/preflight/checker.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently using `just preflight` and attempting server start with/without failures
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- `just preflight` runs online preflight checks (may query model registry)
- `just preflight-offline` runs offline preflight checks (uses cached detection only)
