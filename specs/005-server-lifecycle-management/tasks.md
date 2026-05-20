# Tasks: Server Lifecycle Management

**Feature**: 005-server-lifecycle-management  
**Date**: 2026-05-14  
**Status**: Pending Implementation  
**Total Tasks**: 42

---

## Dependencies

**User Story Completion Order** (independent stories can be parallelized after foundational tasks):
1. **Phase 1: Foundational** → Required for all stories (PID management, port detection)
2. **Phase 2: US1** (P1) → Server start with PID management
3. **Phase 3: US2** (P1) → Server stop with graceful shutdown
4. **Phase 4: US3** (P2) → Server status monitoring
5. **Phase 5: US4** (P2) → Port conflict resolution
6. **Phase 6: Polish** → Cross-cutting concerns (testing, documentation)

**Parallel Opportunities**:
- US3 (status) and US4 (port conflict) can be developed in parallel after Phase 1
- Within each story, [P] tasks can run in parallel
- US1 and US2 have dependencies on Phase 1 foundational tasks

---

## Phase 1: Foundational (Blocking Prerequisites)

- [X] T001 Create scripts/server-lifecycle.py with ServerLifecycleManager class skeleton
- [X] T002 [P] Implement PID file manager in scripts/server-lifecycle.py (create, read, validate, remove)
- [X] T003 [P] Implement atomic PID file writer in scripts/server-lifecycle.py (prevent corruption from concurrent access, use fcntl.flock)
- [X] T004 [P] Implement process validator in scripts/server-lifecycle.py (check if PID is alive using psutil)
- [X] T005 Implement port conflict detector in scripts/server-lifecycle.py (detect port in use via psutil or lsof)
- [X] T006 Implement health endpoint checker in scripts/server-lifecycle.py (query /health endpoint with timeout)
- [X] T006.1 Implement structured lifecycle logging in scripts/server-lifecycle.py (FR-010: log all lifecycle events with configurable log level)

---

## Phase 2: User Story 1 - Server Start with PID Management (P1)

**Story Goal**: Infrastructure operators can start the MLX server with PID file management to reliably track server processes and prevent duplicate starts.

**Independent Test**: Start server, verify PID file creation, attempt duplicate start (should fail), check stale PID cleanup.

- [X] T007 [US1] Implement server-start logic in scripts/server-lifecycle.py (check PID, validate/remove stale, start server)
- [X] T008 [US1] Add PID file creation after successful server startup in scripts/server-lifecycle.py
- [X] T009 [US1] Implement duplicate start prevention in scripts/server-lifecycle.py (check existing PID, verify process alive)
- [X] T010 [US1] Add stale PID file detection and cleanup in scripts/server-lifecycle.py (validate PID, remove if dead process)

---

## Phase 3: User Story 2 - Server Stop with Graceful Shutdown (P1)

**Story Goal**: Infrastructure operators can stop the server with graceful shutdown to drain active requests and release resources properly.

**Independent Test**: Start server, initiate shutdown during active requests, verify requests complete before termination.

- [X] T011 [US2] Implement server-stop logic in scripts/server-lifecycle.py (SIGTERM, wait for graceful period)
- [X] T012 [US2] Add active request draining in scripts/server-lifecycle.py (poll /health endpoint to verify server ready)
- [X] T013 [US2] Implement graceful shutdown timeout handler in scripts/server-lifecycle.py (SIGKILL after timeout)
- [X] T014 [US2] Add PID file cleanup on shutdown in scripts/server-lifecycle.py (remove PID file after process exits)
- [X] T015 [US2] Implement shutdown status reporter in scripts/server-lifecycle.py (log shutdown progress, timeout warnings)

---

## Phase 4: User Story 3 - Server Status Monitoring (P2)

**Story Goal**: Infrastructure operators can check server status to quickly determine if the server is running, healthy, and accepting requests.

**Independent Test**: Start/stop server and verify `just server-status` returns accurate state information.

- [X] T016 [US3] Implement server-status logic in scripts/server-lifecycle.py (check process, query health, format output)
- [X] T017 [US3] Add health endpoint integration in scripts/server-lifecycle.py (query /health, parse response)
- [X] T018 [US3] Implement status formatter in scripts/server-lifecycle.py (display PID, uptime, port, health status)
- [X] T019 [US3] Add degraded status detection in scripts/server-lifecycle.py (running but health check failing)
- [X] T019.1 [US3] Add multi-instance status display in scripts/server-lifecycle.py (read instances.yaml, show all configured instances)

---

## Phase 5: User Story 4 - Port Conflict Resolution (P2)

**Story Goal**: Infrastructure operators have automatic port conflict detection and resolution to avoid manual port hunting.

**Independent Test**: Start process on default port, attempt server start, verify conflict detection and resolution.

- [X] T020 [US4] Add conflict resolution options in scripts/server-lifecycle.py (terminate process or use alternate port) *(Note: Port detection in T005, no duplication)*
- [X] T021 [US4] Implement auto-assign port logic in scripts/server-lifecycle.py (find next available port in range)
- [X] T022 [US4] Add port scan range configuration in scripts/server-lifecycle.py (configurable scan depth, default 10 ports)

---

## Phase 6: Integration with just Recipes

**Story Goal**: Expose all lifecycle management functionality through `just` command bridge as specified in the feature spec.

**Independent Test**: Run `just server-start`, `just server-stop`, `just server-status` and verify correct behavior.

- [X] T023 Add `server-start` recipe to [`justfile`](justfile) (call server-lifecycle.py with config, uses SERVER_PID_FILE)
- [X] T024 Add `server-stop` recipe to [`justfile`](justfile) (call server-lifecycle.py with graceful timeout)
- [X] T025 Add `server-status` recipe to [`justfile`](justfile) (call server-lifecycle.py with formatting)
- [X] T026 [P] Add configuration variables to [`justfile`](justfile) (SERVER_PID_FILE, SERVER_GRACEFUL_TIMEOUT, SERVER_LOG_LEVEL)
- [X] T027 [P] Add helper functions to [`justfile`](justfile) (PID file path resolver, port validator)
- [X] T027.1 Add `server-config` recipe to [`justfile`](justfile) (display current configuration, Constitution Principle IV compliance)

---

## Phase 7: Testing

**Story Goal**: Comprehensive test coverage for all lifecycle management functionality.

**Independent Test**: Run pytest and verify all lifecycle management tests pass.

- [X] T028 [P] Create tests/test_server_lifecycle.py with unit tests for ServerLifecycleManager class
- [X] T029 [P] Add PID file management tests in tests/test_server_lifecycle.py (create, read, validate, stale detection, atomic writes)
- [X] T030 [P] Add port conflict detection tests in tests/test_server_lifecycle.py (mock port usage, conflict resolution)
- [X] T031 Add graceful shutdown tests in tests/test_server_lifecycle.py (mock active requests, timeout handling)
- [X] T032 Add status check tests in tests/test_server_lifecycle.py (mock health endpoint, process state, multi-instance)
- [X] T033 Add integration tests for just recipes in tests/test_server_lifecycle.py (mock subprocess calls)
- [X] T034 Add logging tests in tests/test_server_lifecycle.py (verify FR-010: lifecycle events logged)
- [X] T034.1 Add performance test for NFR-001: Server start <5s (excluding model load) in tests/test_server_lifecycle.py
- [X] T034.2 Add performance test for NFR-002: Status check <2s in tests/test_server_lifecycle.py
- [X] T034.3 Add performance test for NFR-005: Port scan <1s in tests/test_server_lifecycle.py

---

## Phase 8: Documentation

**Story Goal**: Update project documentation with new server lifecycle management capabilities.

**Independent Test**: Verify documentation accurately reflects implemented functionality.

- [X] T035 Update [`OPERATIONS.md`](OPERATIONS.md) with server-start/stop/status recipes and examples
- [X] T036 Update [`README.md`](README.md) with lifecycle management section and quick reference
- [X] T037 Create specs/005-server-lifecycle-management/quickstart.md with usage examples
- [X] T038 Create specs/005-server-lifecycle-management/checklists/requirements.md with completion checklist
- [X] T038.1 Create specs/005-server-lifecycle-management/contracts/server-lifecycle-interface.md (ServerLifecycleManager class interface)

---

## Summary

| Phase | Tasks | Status |
|-------|-------|--------|
| Phase 1: Foundational | T001-T006, T006.1 | Pending |
| Phase 2: US1 - Server Start | T007-T010 | Pending |
| Phase 3: US2 - Server Stop | T011-T015 | Pending |
| Phase 4: US3 - Server Status | T016-T019, T019.1 | Pending |
| Phase 5: US4 - Port Conflict | T020-T022 | Pending |
| Phase 6: just Integration | T023-T027, T027.1 | Pending |
| Phase 7: Testing | T028-T034, T034.1-T034.3 | Pending |
| Phase 8: Documentation | T035-T038, T038.1 | Pending |

**Next Step**: Run `/speckit.implement` to begin implementation starting with Phase 1 foundational tasks.
