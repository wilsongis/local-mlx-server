---
description: "Task list for MLX Server Wrapper implementation"
---

# Tasks: MLX Server Wrapper

**Input**: Design documents from `/specs/004-mlx-server-wrapper/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/, quickstart.md
**Feature**: 004-mlx-server-wrapper
**Date**: 2026-05-14

**Tests**: Tests are NOT included (not explicitly requested in feature specification)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create wrapper script structure in `scripts/mlx_wrapper.py`
- [ ] T002 [P] Create wrapper configuration directory `scripts/wrapper-config/`
- [ ] T003 [P] Create model profiles YAML template in `scripts/wrapper-config/profiles.yaml`
- [ ] T004 [P] Create startup presets YAML template in `scripts/wrapper-config/presets.yaml`
- [ ] T005 Add Click dependency to `pyproject.toml` (click, pyyaml, psutil)
- [ ] T006 [P] Create tests directory structure `tests/test_wrapper.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Implement YAML config loader in `scripts/mlx_wrapper.py` (load profiles and presets)
- [ ] T008 [P] Implement model profile validator in `scripts/mlx_wrapper.py` (validate ModelProfile fields per data-model.md)
- [ ] T009 [P] Implement startup preset validator in `scripts/mlx_wrapper.py` (validate StartupPreset fields per data-model.md)
- [ ] T010 Implement memory checking utility using psutil in `scripts/mlx_wrapper.py`
- [ ] T011 Implement subprocess manager for mlx_lm.server in `scripts/mlx_wrapper.py`
- [ ] T012 Add PID file management for server process tracking in `scripts/mlx_wrapper.py`
- [ ] T013 Integrate wrapper with `just` recipes (update `justfile` with mlx-start, mlx-stop, mlx-status, mlx-health)
- [ ] T014 Implement logging configuration with verbose mode support in `scripts/mlx_wrapper.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Start MLX Server with Health Monitoring (Priority: P1) 🎯 MVP

**Goal**: Infrastructure operators can start the mlx_lm.server with automated health checks, ensuring reliable server operation with failure detection.

**Independent Test**: Can be fully tested by starting the server and verifying health check endpoints return expected status.

### Implementation for User Story 1

- [ ] T015 [US1] Implement `start` subcommand CLI interface in `scripts/mlx_wrapper.py` (Click command with --profile, --port, --host, --preset arguments per contracts/cli-interface.md)
- [ ] T016 [US1] Implement profile validation before startup in `scripts/mlx_wrapper.py` (check profile exists, validate model path)
- [ ] T017 [US1] Implement memory check before startup in `scripts/mlx_wrapper.py` (compare available memory against profile/preset requirements, FR-015)
- [ ] T018 [US1] Implement mlx_lm.server startup with quantization config in `scripts/mlx_wrapper.py` (apply hybrid quantization settings from ModelProfile)
- [ ] T019 [US1] Implement server ready polling in `scripts/mlx_wrapper.py` (poll `/v1/models` endpoint, show progress)
- [ ] T020 [US1] Implement `health` subcommand CLI interface in `scripts/mlx_wrapper.py` (per contracts/cli-interface.md and contracts/health-endpoint.md)
- [ ] T021 [US1] Implement health check endpoint proxy in `scripts/mlx_wrapper.py` (GET /health with HealthStatus entity fields)
- [ ] T022 [US1] Implement health status tracking in `scripts/mlx_wrapper.py` (status: initializing/ready/degraded/down, load_progress_pct, memory_usage_gb)
- [ ] T023 [US1] Implement `status` subcommand in `scripts/mlx_wrapper.py` (check process running, query /v1/models, output human-readable and --json formats)
- [ ] T024 [US1] Implement `stop` subcommand in `scripts/mlx_wrapper.py` (SIGTERM graceful shutdown, --force option, --timeout, cleanup PID file)
- [ ] T025 [US1] Add error handling for startup failures in `scripts/mlx_wrapper.py` (invalid profile, port in use, model load failure with clear error messages)
- [ ] T026 [US1] Integrate OpenAI-compatible API preservation in `scripts/mlx_wrapper.py` (ensure mlx_lm.server args maintain FR-010 compliance)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently - operators can start/stop server and check health

---

## Phase 4: User Story 2 - Model Profile Selection with Hybrid Quantization (Priority: P2)

**Goal**: Infrastructure operators can select model profiles that support per-path hybrid quantization to optimize memory usage for different model architectures.

**Independent Test**: Can be fully tested by selecting different model profiles and verifying the correct quantization configuration is applied per model path.

### Implementation for User Story 2

- [ ] T027 [US2] Implement `list-profiles` subcommand in `scripts/mlx_wrapper.py` (display available profiles with descriptions, --json format)
- [ ] T028 [US2] Implement hybrid quantization path parser in `scripts/mlx_wrapper.py` (parse QuantizationPath entities with pattern, bits, group_size from data-model.md)
- [ ] T029 [US2] Implement per-path quantization application in `scripts/mlx_wrapper.py` (apply different quantization types per model layer/path using MLX quantization API)
- [ ] T030 [US2] Implement KV cache compression config in `scripts/mlx_wrapper.py` (apply kv_cache settings from ModelProfile: quantized, bits)
- [ ] T031 [US2] Implement inference arguments builder in `scripts/mlx_wrapper.py` (build mlx_lm.server args from ModelProfile.inference_args: max_context_length, temperature, batch_size)
- [ ] T032 [US2] Add validation for invalid profile names in `scripts/mlx_wrapper.py` (return error listing available profiles, FR-007, FR-008)
- [ ] T033 [US2] Implement quantization type validation in `scripts/mlx_wrapper.py` (validate bits are 4/8/16, group_size is power of 2 per data-model.md)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - profile selection with hybrid quantization is functional

---

## Phase 5: User Story 3 - 120B+ Model Memory Optimization Presets (Priority: P2)

**Goal**: Infrastructure operators can use startup argument presets for 120B+ models to reliably serve large models on Apple Silicon with constrained memory.

**Independent Test**: Can be fully tested by starting server with 120B+ preset and verifying memory usage stays within available bounds while maintaining inference capability.

### Implementation for User Story 3

- [ ] T034 [US3] Implement `list-presets` subcommand in `scripts/mlx_wrapper.py` (display available presets with memory requirements and model size targets)
- [ ] T035 [US3] Implement preset loader in `scripts/mlx_wrapper.py` (load StartupPreset from presets.yaml, validate references to ModelProfile)
- [ ] T036 [US3] Implement preset argument merger in `scripts/mlx_wrapper.py` (apply preset defaults, allow explicit arguments to override preset values, FR-006)
- [ ] T037 [US3] Implement 120B+ memory optimization in `scripts/mlx_wrapper.py` (enforce batch_size=1, limit max_context_length≤2048 for 120B+ presets per data-model.md)
- [ ] T038 [US3] Implement memory warning system in `scripts/mlx_wrapper.py` (warn operator when available memory insufficient, suggest alternative presets, FR-015)
- [ ] T039 [US3] Add preset validation for model size class in `scripts/mlx_wrapper.py` (validate target_memory_gb ≤ 128, check batch_size rules per data-model.md)

**Checkpoint**: All user stories should now be independently functional - presets for 120B+ models work correctly

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Update `README.md` with MLX wrapper documentation (usage examples, CLI commands, configuration)
- [ ] T041 [P] Update `OPERATIONS.md` with wrapper operational procedures (start/stop/health workflows via just recipes)
- [ ] T042 Code cleanup and refactoring in `scripts/mlx_wrapper.py` (extract helper functions, improve error messages)
- [ ] T043 Performance optimization for health checks in `scripts/mlx_wrapper.py` (ensure <1s response time per SC-002)
- [ ] T044 Add API key authentication support in `scripts/mlx_wrapper.py` (FR-013, pass --api-key to mlx_lm.server if supported, otherwise implement wrapper-level auth)
- [ ] T045 Validate startup time for 120B+ models in `scripts/mlx_wrapper.py` (ensure <5min startup per SC-001)
- [ ] T046 Run quickstart.md validation (verify all examples in quickstart.md work correctly)
- [ ] T047 Update `justfile` with additional helper recipes (mlx-list-profiles, mlx-list-presets)
- [ ] T048 Implement metrics endpoint in `scripts/mlx_wrapper.py` (FR-011: expose memory_usage_gb, request_count, avg_latency via /metrics endpoint or health response extension)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P2)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 (profile validation) but should be independently testable
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - May integrate with US2 (preset uses profile) but should be independently testable

### Within Each User Story

- CLI interface before implementation details
- Validation before server startup
- Health endpoint after server startup works
- Profile/listing commands can be parallel with core implementation

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Different user stories can be worked on in parallel by different team members
- US2 and US3 can be developed in parallel after US1 is complete (they have some dependency on profile/preset structures)

---

## Parallel Example: User Story 1

```bash
# Launch foundational utilities together:
Task: T010 - Implement memory checking utility using psutil in scripts/mlx_wrapper.py
Task: T012 - Add PID file management for server process tracking in scripts/mlx_wrapper.py

# Launch CLI commands in parallel (different subcommands):
Task: T015 [US1] - Implement start subcommand CLI interface in scripts/mlx_wrapper.py
Task: T020 [US1] - Implement health subcommand CLI interface in scripts/mlx_wrapper.py
Task: T023 [US1] - Implement status subcommand in scripts/mlx_wrapper.py
Task: T024 [US1] - Implement stop subcommand in scripts/mlx_wrapper.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
   - Start server with profile
   - Verify health checks work
   - Test stop command
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
   - Developer B: User Story 2 (after US1 foundational pieces done)
   - Developer C: User Story 3 (after US2 profile structures done)
3. Stories complete and integrate independently

---

## Summary

- **Total Tasks**: 47
- **Phase 1 (Setup)**: 6 tasks
- **Phase 2 (Foundational)**: 8 tasks
- **Phase 3 (US1 - P1)**: 12 tasks
- **Phase 4 (US2 - P2)**: 7 tasks
- **Phase 5 (US3 - P2)**: 6 tasks
- **Phase 6 (Polish)**: 8 tasks

### Parallel Opportunities Identified
- 14 tasks marked [P] can run in parallel where dependencies allow
- All 3 user stories can be developed in parallel after Phase 2 (with some sequencing for shared components)
- Within each story, multiple subcommands can be implemented in parallel

### Independent Test Criteria
- **US1**: Start server with profile, verify health endpoint returns ready status, test stop command
- **US2**: Select different profiles, verify hybrid quantization applied correctly per path
- **US3**: Start with 120B+ preset, verify memory usage within bounds, test preset override behavior

### Suggested MVP Scope
**User Story 1 only** (Phase 3: T015-T026) - Provides core server lifecycle management with health monitoring. This delivers immediate operational value: operators can start/stop the MLX server and monitor its health.

---

## Notes

- [P] tasks = different files or independent code sections, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify functionality after each phase completion
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- All tasks target single file `scripts/mlx_wrapper.py` except config YAMLs and justfile updates
