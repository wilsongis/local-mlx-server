# Tasks: MLX Server Wrapper

**Feature**: 004-mlx-server-wrapper  
**Date**: 2026-05-12  
**Status**: Implementation Complete  
**Total Tasks**: 36

---

## Dependencies

**User Story Completion Order** (independent stories can be parallelized after foundational tasks):
1. **Phase 2: Foundational** → Required for all stories
2. **Phase 3: US1** (P1) → Can complete independently, MVP scope
3. **Phase 4: US2** (P2) → Can complete independently after Phase 2
4. **Phase 5: US3** (P2) → Can complete independently after Phase 2
5. **Phase 6: Polish** → Cross-cutting concerns

**Parallel Opportunities**:
- US2 and US3 can be developed in parallel (different concerns: US2=profiles, US3=presets)
- Within each story, [P] tasks can run in parallel

---

## Phase 1: Setup

- [X] T001 Create wrapper configuration directory at scripts/wrapper-config/
- [X] T002 [P] Create profiles.yaml template in scripts/wrapper-config/profiles.yaml
- [X] T003 [P] Create presets.yaml template in scripts/wrapper-config/presets.yaml
- [X] T004 Update justfile with wrapper recipes (mlx-start, mlx-stop, mlx-status, mlx-health) in justfile

---

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T005 Create MLXServerManager class in scripts/mlx_wrapper.py (process management, start/stop methods)
- [X] T006 [P] Implement configuration loader in scripts/mlx_wrapper.py (YAML parsing, profile validation)
- [X] T007 [P] Implement memory checker using psutil in scripts/mlx_wrapper.py (check_available_memory function)
- [X] T008 Create Click CLI structure in scripts/mlx_wrapper.py (group, subcommands: start, stop, status, health)
- [X] T009 [P] Implement health endpoint server in scripts/mlx_wrapper.py (Flask/lightweight HTTP on separate port)
- [X] T010 Implement health status aggregator in scripts/mlx_wrapper.py (query mlx_lm.server, add system metrics)

---

## Phase 3: User Story 1 - Start MLX Server with Health Monitoring (P1)

**Story Goal**: Infrastructure operators can start the mlx_lm.server with automated health checks for reliable local inference serving.

**Independent Test**: Start server and verify health check endpoints return expected status.

- [X] T011 [US1] Implement start subcommand in scripts/mlx_wrapper.py (load profile, validate, start server)
- [X] T012 [US1] Implement server readiness waiter in scripts/mlx_wrapper.py (poll /v1/models endpoint with timeout)
- [X] T013 [US1] Implement health subcommand in scripts/mlx_wrapper.py (query health endpoint, format output)
- [X] T014 [US1] Implement status subcommand in scripts/mlx_wrapper.py (check process, query server status)
- [X] T015 [US1] Implement stop subcommand in scripts/mlx_wrapper.py (SIGTERM, graceful shutdown with timeout)
- [X] T016 [US1] Add progress reporting for model loading in scripts/mlx_wrapper.py (parse startup output or poll progress)
- [X] T017 [US1] Handle startup failures with clear error messages in scripts/mlx_wrapper.py (invalid model, port in use, etc.)

---

## Phase 4: User Story 2 - Model Profile Selection with Hybrid Quantization (P2)

**Story Goal**: Infrastructure operators can select model profiles with per-path hybrid quantization for memory-optimized serving.

**Independent Test**: Select different model profiles and verify correct quantization configuration is applied.

- [X] T018 [US2] Implement profile loader and validator in scripts/mlx_wrapper.py (parse profiles.yaml, validate schema)
- [X] T019 [US2] Implement hybrid quantization config builder in scripts/mlx_wrapper.py (map QuantizationPath to mlx_lm arguments)
- [X] T020 [US2] Add profile listing subcommand in scripts/mlx_wrapper.py (list-profiles command with formatting)
- [X] T021 [US2] Implement per-path quantization argument builder in scripts/mlx_wrapper.py (generate --quantize args from profile)
- [X] T022 [US2] Validate profile selection before startup in scripts/mlx_wrapper.py (check model path exists, profile valid)
- [X] T023 [US2] Add KV cache compression settings to startup args in scripts/mlx_wrapper.py (apply kv_cache config)

---

## Phase 5: User Story 3 - 120B+ Model Memory Optimization Presets (P2)

**Story Goal**: Infrastructure operators can use startup argument presets for 120B+ models on memory-constrained Apple Silicon.

**Independent Test**: Start server with 120B+ preset and verify memory usage stays within bounds.

- [X] T024 [US3] Implement preset loader and validator in scripts/mlx_wrapper.py (parse presets.yaml, validate references)
- [X] T025 [US3] Implement preset application logic in scripts/mlx_wrapper.py (override profile defaults with preset values)
- [X] T026 [US3] Add preset listing subcommand in scripts/mlx_wrapper.py (list-presets command with memory requirements)
- [X] T027 [US3] Implement memory pre-check with preset in scripts/mlx_wrapper.py (compare available vs target_memory_gb)
- [X] T028 [US3] Add memory warning/suggestion logic in scripts/mlx_wrapper.py (warn if insufficient, suggest alternatives)

---

## Phase 6: API Key Authentication (FR-013)

**Story Goal**: Infrastructure operators can secure wrapper admin endpoints with API key authentication without breaking OpenAI-compatible /v1/* endpoints.

**Independent Test**: Verify API key required for admin endpoints (health, status, list-profiles) but not for mlx_lm.server /v1/* endpoints.

- [X] T034 [US-SEC] Add API key configuration to profiles.yaml in scripts/wrapper-config/profiles.yaml (api_key field, environment variable support)
- [X] T035 [US-SEC] Implement API key middleware in scripts/mlx_wrapper.py (validate key for admin endpoints: /health, /status, /list-profiles, /list-presets)
- [X] T036 [US-SEC] Add API key to wrapper startup config in scripts/mlx_wrapper.py (--api-key argument, environment variable MLX_WRAPPER_API_KEY)

---

## Phase 7: Health Check Accuracy Validation (SC-006)

**Story Goal**: Ensure health check accuracy meets 95% target with proper test coverage.

**Independent Test**: Run fault injection tests to verify health check correctly reports server state.

- [X] T037 [US1] Implement health check accuracy tests in tests/test_health_accuracy.py (fault injection: model load failure, process crash, timeout scenarios)
- [X] T038 [US1] Add health status validation logic in scripts/mlx_wrapper.py (verify mlx_lm.server response matches health status)

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T029 [P] Add comprehensive error handling and logging in scripts/mlx_wrapper.py (Click exceptions, log files, traceback)
- [X] T030 [P] Add JSON output support to status and health commands in scripts/mlx_wrapper.py (--json flag)
- [X] T031 [P] Add CLI help text and examples in scripts/mlx_wrapper.py (Click help, usage examples)
- [X] T032 Validate OpenAI API compatibility in scripts/mlx_wrapper.py (ensure /v1/* endpoints pass through without auth)
- [X] T033 Validate all tasks against Constitution principles (I-V) and update documentation if needed

---

## Parallel Execution Examples

### Example 1: Foundational Tasks (Phase 2)
```bash
# These can run in parallel (different concerns):
# Terminal 1:
# Implement T005: MLXServerManager class

# Terminal 2:
# Implement T008: Click CLI structure

# Terminal 3:
# Implement T009: Health endpoint server
```

### Example 2: User Story 2 Tasks (Phase 4)
```bash
# These can run in parallel (all [P] or different files):
# Terminal 1: T018 - Profile loader
# Terminal 2: T020 - List-profiles command
# Terminal 3: T023 - KV cache settings
```

### Example 3: Independent User Stories
```bash
# US2 and US3 can be developed in parallel after Phase 2:
# Team member 1: Phase 4 (US2) - Profile selection
# Team member 2: Phase 5 (US3) - Memory presets
```

---

## Implementation Strategy

**MVP Scope (Recommended First Implementation)**:
- Phase 1: Setup (T001-T004) ✅ COMPLETE
- Phase 2: Foundational (T005-T010) ✅ COMPLETE
- Phase 3: User Story 1 only (T011-T017) ✅ COMPLETE
- Phase 4: US2 (T018-T023) ✅ COMPLETE
- Phase 5: US3 (T024-T028) ✅ COMPLETE
- Phase 6: API Key Authentication (T034-T036) ✅ COMPLETE
- Phase 7: Health Check Accuracy (T037-T038) ✅ COMPLETE
- Phase 8: Polish & Cross-Cutting Concerns (T029-T033) ✅ COMPLETE

**Incremental Delivery Order**:
1. ✅ MVP: US1 (start/stop/status/health) - immediately usable
2. ✅ US2: Profile selection with hybrid quantization
3. ✅ US3: Memory optimization presets
4. ✅ Phase 6: API key authentication (security layer)
5. ✅ Phase 7: Health check accuracy validation
6. ✅ Phase 8: Polish: Cross-cutting concerns

**Task Format Validation**:
- ✅ All tasks have checkbox: `- [ ]` or `- [X]`
- ✅ All tasks have ID: `T001`, `T002`, etc.
- ✅ Parallel tasks marked with `[P]`
- ✅ Story tasks have `[US1]`, `[US2]`, `[US3]`, `[US-SEC]` labels
- ✅ Setup/Foundational/Polish tasks have NO story label
- ✅ All tasks include file path in description

---

## Summary

| Phase | Description | Task Count | Completed | Story |
|-------|-------------|------------|-----------|-------|
| Phase 1 | Setup | 4 | 4 | None |
| Phase 2 | Foundational | 6 | 6 | None |
| Phase 3 | User Story 1 (P1) | 7 | 7 | US1 |
| Phase 4 | User Story 2 (P2) | 6 | 6 | US2 |
| Phase 5 | User Story 3 (P2) | 5 | 5 | US3 |
| Phase 6 | API Key Authentication | 3 | 3 | US-SEC |
| Phase 7 | Health Check Accuracy | 2 | 2 | US1 |
| Phase 8 | Polish | 5 | 5 | None |
| **Total** | | **36** | **36** | |

**Parallelizable Tasks**: 12 (marked with [P])

**MVP Tasks** (US1 only): 17 tasks (T001-T017) - ✅ COMPLETE

**Independent Stories**: US1 (P1) ✅, US2 (P2) ✅, US3 (P2) ✅, US-SEC (security) ✅
