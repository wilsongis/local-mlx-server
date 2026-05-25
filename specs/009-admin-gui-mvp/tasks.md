# Tasks: Admin GUI MVP

**Input**: Design documents from `/specs/009-admin-gui-mvp/`

**Prerequisites**: plan.md, spec.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are NOT included (not explicitly requested in feature specification)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create gui/ directory structure per implementation plan in `gui/`, `gui/templates/`, `gui/static/`, `gui/services/`, `gui/tests/`
- [x] T002 [P] Create `gui/__init__.py` with empty file
- [x] T003 [P] Create `gui/services/__init__.py` with empty file
- [x] T004 Add Flask dependency to pyproject.toml if not present (check existing dependencies)
- [x] T005 [P] Create base HTML template `gui/templates/base.html` with common layout and navigation

**Checkpoint**: Directory structure and base template ready

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Implement data models (ServerStatus, ModelInfo, LogEntry, ServerAction) in `gui/services/models.py` per data-model.md Python classes
- [x] T007 Implement just command interface `run_just_command()` in `gui/services/server_control.py` per contracts/just-command-interface.md
- [x] T008 Implement health check polling `check_server_health()` in `gui/services/status_monitor.py` querying http://localhost:8000/health
- [x] T009 [P] Implement log reading service `read_logs()` in `gui/services/log_reader.py` to access server logs
- [x] T010 Create Flask application entry point `gui/app.py` with app initialization, MLX_HEALTH_URL, and GUI_PORT=8080

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - View server status and basic controls (Priority: P1) 🎯 MVP

**Goal**: Display server running/stopped status with Start/Stop buttons that execute `just start` and `just stop` commands

**Independent Test**: Can be fully tested by checking server status indicator and verifying start/stop buttons trigger the corresponding `just` commands, delivering immediate server control value

### Implementation for User Story 1

- [x] T011 [US1] Create main dashboard template `gui/templates/index.html` with status indicator and Start/Stop buttons per contracts/http-endpoints.md
- [x] T012 [US1] Implement GET `/` route in `gui/app.py` rendering index.html with server_status, model_info, last_checked context
- [x] T013 [US1] Implement GET `/api/status` JSON endpoint in `gui/app.py` returning status, timestamp, model, error per contracts/http-endpoints.md
- [x] T014 [US1] Implement POST `/api/start` endpoint in `gui/app.py` calling `run_just_command('start')` per contracts/http-endpoints.md
- [x] T015 [US1] Implement POST `/api/stop` endpoint in `gui/app.py` calling `run_just_command('stop')` per contracts/http-endpoints.md
- [x] T016 [US1] Create minimal JavaScript `gui/static/app.js` for polling `/api/status` every 5 seconds and updating status indicator
- [x] T017 [US1] Create minimal CSS `gui/static/style.css` with .running and .stopped status indicator styles

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently - MVP complete

---

## Phase 4: User Story 2 - View current model information (Priority: P2)

**Goal**: Display model name and quantization configuration when server is running

**Independent Test**: Can be fully tested by displaying model name and quantization info after server starts, delivering model awareness value

### Implementation for User Story 2

- [x] T018 [US2] Extend `gui/services/status_monitor.py` to extract ModelInfo (name, quantization_config) from health endpoint response
- [x] T019 [US2] Update `gui/templates/index.html` to display model information section when server is running (model name, quantization config)
- [x] T020 [US2] Update GET `/api/status` in `gui/app.py` to include model.name and model.quantization_config in JSON response
- [x] T021 [US2] Add "No model loaded" indication in `gui/templates/index.html` when server is stopped

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - View server logs or recent activity (Priority: P3)

**Goal**: Display recent server log output for quick diagnosis

**Independent Test**: Can be fully tested by displaying a scrolling log panel that shows recent stdout/stderr from the server process, delivering diagnostic value

### Implementation for User Story 3

- [x] T022 [US3] Create log viewer template `gui/templates/logs.html` with scrolling log display per contracts/http-endpoints.md
- [x] T023 [US3] Implement GET `/logs` route in `gui/app.py` rendering logs.html with log_entries and server_running context
- [x] T024 [US3] Extend `gui/services/log_reader.py` to parse log lines into LogEntry objects with timestamp, message, level, source
- [x] T025 [US3] Add link to logs page in `gui/templates/base.html` navigation
- [ ] T026 [US3] Update GET `/api/status` or create separate endpoint to provide recent log entries for polling (optional enhancement)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T027 [P] Add error handling and user feedback for failed `just` commands in `gui/app.py` endpoints (display error messages per FR-006)
- [x] T028 Handle edge cases: server started outside GUI, `just` command not found, command timeout in `gui/services/server_control.py`
- [x] T029 [P] Add HTML meta refresh fallback or improve JavaScript polling in `gui/static/app.js` for reliability
- [x] T030 Update `gui/app.py` to run on localhost only (host='localhost') for security per FR-007
- [x] T031 Verify all templates extend `gui/templates/base.html` and have consistent styling
- [x] T032 Run quickstart.md validation: create test instance, verify all user stories work end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed sequentially in priority order (P1 → P2 → P3)
  - Or in parallel if team capacity allows (each is independently testable)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories - **MVP**
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May use ServerStatus from US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Models/Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# These tasks can run in parallel (different files, no dependencies):
# Terminal 1:
# Create gui/templates/index.html (T011)

# Terminal 2:
# Create gui/static/app.js (T016)

# Terminal 3:
# Create gui/static/style.css (T017)

# Then sequentially (after T011, T016, T017 complete):
# Implement routes in gui/app.py (T012, T013, T014, T015)
```

---

## Summary

- **Total Tasks**: 32
- **User Story 1 (P1 - MVP)**: 7 tasks (T011-T017)
- **User Story 2 (P2)**: 4 tasks (T018-T021)
- **User Story 3 (P3)**: 5 tasks (T022-T026)
- **Setup**: 5 tasks (T001-T005)
- **Foundational**: 5 tasks (T006-T010)
- **Polish**: 6 tasks (T027-T032)
- **Parallel Opportunities**: 10 tasks marked [P] can run in parallel
- **MVP Scope**: User Story 1 only (T011-T017) delivers core value - server status visibility and control

---

## Implementation Strategy

1. **Start with MVP**: Implement Phase 1 → Phase 2 → Phase 3 (User Story 1) for immediate value
2. **Incremental Delivery**: Add User Story 2, then User Story 3 as time allows
3. **Test Each Story Independently**: Each user story phase should be fully functional before moving to the next
4. **Polish Last**: Apply cross-cutting improvements only after core functionality is complete
