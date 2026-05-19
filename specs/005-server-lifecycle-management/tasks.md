# Tasks: Server Lifecycle Management

**Feature**: 005-server-lifecycle-management  
**Date**: 2026-05-14  
**Status**: Pending Implementation  
**Total Tasks**: 20

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

- [ ] T001 Create scripts/server-lifecycle.py with ServerLifecycleManager class skeleton
- [ ] T002 [P] Implement PID file manager in scripts/server-lifecycle.py (create, read, validate, remove)
- [ ] T003 [P] Implement atomic PID file writer in scripts/server-lifecycle.py (prevent corruption from concurrent access)
- [ ] T004 [P] Implement process validator in scripts/server-lifecycle.py (check if PID is alive using psutil)
- [ ] T005 Implement port conflict detector in scripts/server-lifecycle.py (detect port in use via psutil or lsof)
- [ ] T006 Implement health endpoint checker in scripts/server-lifecycle.py (query /health endpoint with timeout)

---

## Phase 2: User Story 1 - Server Start with PID Management (P1)

**Story Goal**: Infrastructure operators can start the MLX server with PID file management to reliably track server processes and prevent duplicate starts.

**Independent Test**: Start server, verify PID file creation, attempt duplicate start (should fail), check stale PID cleanup.

- [ ] T007 [US1] Implement server-start logic in scripts/server-lifecycle.py (check PID, validate/remove stale, start server)
- [ ] T008 [US1] Add PID file creation after successful server startup in scripts/server-lifecycle.py
- [ ] T009 [US1] Implement duplicate start prevention in scripts/server-lifecycle.py (check existing PID, verify process alive)
- [ ] T010 [US1] Add stale PID file detection and cleanup in scripts/server-lifecycle.py (validate PID, remove if dead process)

---

## Phase 3: User Story 2 - Server Stop with Graceful Shutdown (P1)

**Story Goal**: Infrastructure operators can stop the server with graceful shutdown to drain active requests and release resources properly.

**Independent Test**: Start server, initiate shutdown during active requests, verify requests complete before termination.

- [ ] T011 [US2] Implement server-stop logic in scripts/server-lifecycle.py (SIGTERM, wait for graceful period)
- [ ] T012 [US2] Add active request draining in scripts/server-lifecycle.py (poll for in-flight requests before shutdown)
- [ ] T013 [US2] Implement graceful shutdown timeout handler in scripts/server-lifecycle.py (SIGKILL after timeout)
- [ ] T014 [US2] Add PID file cleanup on shutdown in scripts/server-lifecycle.py (remove PID file after process exits)
- [ ] T015 [US2] Implement shutdown status reporter in scripts/server-lifecycle.py (log shutdown progress, timeout warnings)

---

## Phase 4: User Story 3 - Server Status Monitoring (P2)

**Story Goal**: Infrastructure operators can check server status to quickly determine if the server is running, healthy, and accepting requests.

**Independent Test**: Start/stop server and verify `just server-status` returns accurate state information.

- [ ] T016 [US3] Implement server-status logic in scripts/server-lifecycle.py (check process, query health, format output)
- [ ] T017 [US3] Add health endpoint integration in scripts/server-lifecycle.py (query /health, parse response)
- [ ] T018 [US3] Implement status formatter in scripts/server-lifecycle.py (display PID, uptime, port, health status)
- [ ] T019 [US3] Add degraded status detection in scripts/server-lifecycle.py (running but health check failing)

---

## Phase 5: User Story 4 - Port Conflict Resolution (P2)

**Story Goal**: Infrastructure operators have automatic port conflict detection and resolution to avoid manual port hunting.

**Independent Test**: Start process on default port, attempt server start, verify conflict detection and resolution.

- [ ] T020 [US4] Implement port conflict detector in scripts/server-lifecycle.py (scan port, identify conflicting process)
- [ ] T021 [US4] Add conflict resolution options in scripts/server-lifecycle.py (terminate process or use alternate port)
- [ ] T022 [US4] Implement auto-assign port logic in scripts/server-lifecycle.py (find next available port in range)
- [ ] T023 [US4] Add port scan range configuration in scripts/server-lifecycle.py (configurable scan depth, default 10 ports)

---

## Phase 6: Integration with just Recipes

**Story Goal**: Expose all lifecycle management functionality through `just` command bridge as specified in the feature spec.

**Independent Test**: Run `just server-start`, `just server-stop`, `just server-status` and verify correct behavior.

- [ ] T024 Add `server-start` recipe to [`justfile`](justfile) (call server-lifecycle.py with config)
- [ ] T025 Add `server-stop` recipe to [`justfile`](justfile) (call server-lifecycle.py with graceful timeout)
- [ ] T026 Add `server-status` recipe to [`justfile`](justfile) (call server-lifecycle.py with formatting)
- [ ] T027 [P] Add configuration variables to [`justfile`](justfile) (PID file path, default port, timeout values)
- [ ] T028 [P] Add helper functions to [`justfile`](justfile) (PID file path resolver, port validator)

---

## Phase 7: Testing

**Story Goal**: Comprehensive test coverage for all lifecycle management functionality.

**Independent Test**: Run pytest and verify all lifecycle management tests pass.

- [ ] T029 [P] Create tests/test_server_lifecycle.py with unit tests for ServerLifecycleManager class
- [ ] T030 [P] Add PID file management tests in tests/test_server_lifecycle.py (create, read, validate, stale detection)
- [ ] T031 [P] Add port conflict detection tests in tests/test_server_lifecycle.py (mock port usage, conflict resolution)
- [ ] T032 Add graceful shutdown tests in tests/test_server_lifecycle.py (mock active requests, timeout handling)
- [ ] T033 Add status check tests in tests/test_server_lifecycle.py (mock health endpoint, process state)
- [ ] T034 Add integration tests for just recipes in tests/test_server_lifecycle.py (mock subprocess calls)

---

## Phase 8: Documentation

**Story Goal**: Update project documentation with new server lifecycle management capabilities.

**Independent Test**: Verify documentation accurately reflects implemented functionality.

- [ ] T035 Update [`OPERATIONS.md`](OPERATIONS.md) with server-start/stop/status recipes and examples
- [ ] T036 Update [`README.md`](README.md) with lifecycle management section and quick reference
- [ ] T037 Create specs/005-server-lifecycle-management/quickstart.md with usage examples
- [ ] T038 Create specs/005-server-lifecycle-management/checklists/requirements.md with completion checklist

---

## Summary

| Phase | Tasks | Status |
|-------|-------|--------|
| Phase 1: Foundational | T001-T006 | Pending |
| Phase 2: US1 - Server Start | T007-T010 | Pending |
| Phase 3: US2 - Server Stop | T011-T015 | Pending |
| Phase 4: US3 - Server Status | T016-T019 | Pending |
| Phase 5: US4 - Port Conflict | T020-T023 | Pending |
| Phase 6: just Integration | T024-T028 | Pending |
| Phase 7: Testing | T029-T034 | Pending |
| Phase 8: Documentation | T035-T038 | Pending |

**Next Step**: Run `/speckit.implement` to begin implementation starting with Phase 1 foundational tasks.
