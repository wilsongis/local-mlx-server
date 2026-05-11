---
description: "Task list for Operations Runbook feature"
---

# Tasks: Operations Runbook

**Input**: Design documents from `/specs/003-operations-runbook/`
**Prerequisites**: plan.md, spec.md, data-model.md, quickstart.md
**Feature**: Documentation-only update to OPERATIONS.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Extension Hooks

**Optional Pre-Hook**: git
Command: `/speckit.git.commit`
Description: Auto-commit before task generation

Prompt: Commit outstanding changes before task generation?
To execute: `/speckit.git.commit`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Documentation setup and inventory

- [ ] T001 Inventory all just recipes in justfile (default, start, build, run, status, stop, init, lint, test, verify, security-check)
- [ ] T002 [P] Read current OPERATIONS.md to identify sections to preserve or restructure
- [ ] T003 [P] Read AGENTS.md to confirm operational charter and terminology standards

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core documentation structure that MUST be complete before user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create OPERATIONS.md section structure: Just Recipe Reference, Troubleshooting Guide, Model Profile Decision Tree, Developer Guidelines
- [ ] T005 Define documentation standards: use "just recipe" canonical terminology, include file paths, follow markdown best practices

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Document all just recipes with examples and edge cases (Priority: P1) 🎯 MVP

**Goal**: Document all `just` recipes with command syntax, required arguments, examples, edge cases, and developer contribution guidelines.

**Independent Test**: Can be fully tested by reviewing OPERATIONS.md to confirm every `just` recipe in justfile is documented with usage examples and edge case handling.

### Implementation for User Story 1

- [ ] T006 [US1] Document `default` recipe in OPERATIONS.md (show available commands)
- [ ] T007 [US1] Document `start` recipe in OPERATIONS.md with container startup example and edge cases
- [ ] T008 [US1] Document `build` recipe in OPERATIONS.md with build example and error handling
- [ ] T009 [US1] Document `run` recipe in OPERATIONS.md with native startup example, arguments (MODEL_PATH, HOST, PORT, MAX_TOKENS)
- [ ] T010 [US1] Document `status` recipe in OPERATIONS.md with container status example
- [ ] T011 [US1] Document `stop` recipe in OPERATIONS.md with stop example and edge cases
- [ ] T012 [US1] Document `init` recipe in OPERATIONS.md with uv venv and install example
- [ ] T013 [US1] Document `lint` recipe in OPERATIONS.md with ruff check/format example
- [ ] T014 [US1] Document `test` recipe in OPERATIONS.md with pytest example
- [ ] T015 [US1] Document `verify` recipe in OPERATIONS.md with lint+test example
- [ ] T016 [US1] Document `security-check` recipe in OPERATIONS.md with script execution example
- [ ] T017 [US1] Create Developer Guidelines section in OPERATIONS.md: justfile contribution standards, recipe naming conventions (kebab-case), testing requirements for new recipes
- [ ] T018 [US1] Add edge cases for each recipe: invalid arguments, error conditions, recovery steps in OPERATIONS.md

**Checkpoint**: At this point, User Story 1 should be fully functional - all just recipes documented with examples and edge cases.

---

## Phase 4: User Story 2 - Create troubleshooting guide for common startup/memory issues (Priority: P1)

**Goal**: Create structured troubleshooting guide covering startup failures, memory issues (OOM, KV cache overflow, quantization failures), and port conflicts.

**Independent Test**: Can be fully tested by simulating common failure scenarios (OOM, port conflicts, model load failures) and verifying the guide provides correct resolution steps.

### Implementation for User Story 2

- [ ] T019 [US2] Create "Startup Failures" section in OPERATIONS.md troubleshooting guide: server fails to start, model load failures, container startup issues (5+ scenarios per FR-004)
- [ ] T020 [US2] Create "Memory Issues" section in OPERATIONS.md: OOM errors, KV cache overflow, quantization failures (3+ scenarios per FR-005)
- [ ] T021 [US2] Create "Port Conflicts" section in OPERATIONS.md: identify and terminate conflicting processes
- [ ] T022 [US2] Add root cause analysis for each troubleshooting scenario in OPERATIONS.md
- [ ] T023 [US2] Add resolution steps (ordered list) for each scenario in OPERATIONS.md
- [ ] T024 [US2] Add prevention tips for each scenario in OPERATIONS.md
- [ ] T025 [US2] Link relevant just recipes to troubleshooting scenarios in OPERATIONS.md (e.g., `just doctor`, `just status`)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - recipes documented AND troubleshooting guide complete.

---

## Phase 5: User Story 3 - Define model profile selection decision tree (48GB vs 64GB vs 96GB tiers) (Priority: P1)

**Goal**: Create decision tree for operators to select correct model profile based on system memory, with quantifiable metrics per tier.

**Independent Test**: Can be fully tested by verifying the decision tree correctly maps system memory tiers to recommended profiles with quantifiable rationale.

### Implementation for User Story 3

- [ ] T026 [US3] Create "Model Profile Decision Tree" section in OPERATIONS.md
- [ ] T027 [US3] Document 48GB tier profile in OPERATIONS.md: ~15 tok/s, 2K context, ~42GB used (per FR-007)
- [ ] T028 [US3] Document 64GB tier profile in OPERATIONS.md: ~22 tok/s, 4K context, ~56GB used (per FR-007)
- [ ] T029 [US3] Document 96GB tier profile in OPERATIONS.md: ~30 tok/s, 8K context, ~80GB used (per FR-007)
- [ ] T030 [US3] Add decision tree logic to OPERATIONS.md: lower-tier fallback rule for between-tier systems (e.g., 56GB → 48GB profile per FR-011)
- [ ] T031 [US3] Add memory check commands to decision tree in OPERATIONS.md: `system_profiler SPHardwareDataType | grep "Memory:"`
- [ ] T032 [US3] Document quantization configuration per profile in OPERATIONS.md: weight compression, KV cache settings

**Checkpoint**: All user stories should now be independently functional - recipes documented, troubleshooting guide complete, decision tree defined.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Review OPERATIONS.md for consistent use of "just recipe" terminology (100% compliance per SC-008)
- [ ] T034 [P] Validate all file paths and cross-references in OPERATIONS.md
- [ ] T035 Ensure OPERATIONS.md follows AGENTS.md infrastructure-only scope (no full-stack components)
- [ ] T036 Validate FR-001 through FR-011 compliance in OPERATIONS.md
- [ ] T037 Validate SC-001 through SC-008 success criteria in OPERATIONS.md
- [ ] T038 Update quickstart.md if OPERATIONS.md structure changes affect operator/developer guides
- [ ] T039 Run `just verify` to ensure documentation changes don't break linting/tests

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P1 → P1, all same priority)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Independent of US1
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) - Independent of US1/US2

### Within Each User Story

- Document recipes/examples before edge cases
- Troubleshooting scenarios before resolution steps
- Decision tree structure before tier details
- Story complete before moving to next

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T002, T003)
- All Foundational tasks can run in parallel (T004, T005)
- Once Foundational phase completes, all three user stories can start in parallel (if team capacity allows)
- All recipe documentation tasks in US1 marked [US1] can be worked on in parallel by different team members (T006-T016)
- Troubleshooting scenarios in US2 can be documented in parallel (T019-T025)
- Decision tree components in US3 can be built in parallel (T026-T032)
- Polish tasks marked [P] can run in parallel (T033, T034)

---

## Parallel Example: User Story 1

```bash
# Team of 3 working on User Story 1 in parallel:
# Person 1: Core recipes (T006-T011)
# Person 2: Maintenance recipes (T012-T016)
# Person 3: Developer guidelines (T017-T018)
```

---

## Extension Hooks

**Optional Hook**: git
Command: `/speckit.git.commit`
Description: Auto-commit after task generation

Prompt: Commit task changes?
To execute: `/speckit.git.commit`

---

## Task Summary

- **Total Tasks**: 39
- **User Story 1 (US1)**: 13 tasks (T006-T018)
- **User Story 2 (US2)**: 7 tasks (T019-T025)
- **User Story 3 (US3)**: 7 tasks (T026-T032)
- **Setup**: 3 tasks (T001-T003)
- **Foundational**: 2 tasks (T004-T005)
- **Polish**: 7 tasks (T033-T039)

## Parallel Opportunities

- 18 tasks marked [P] for parallel execution
- All 3 user stories can run in parallel after Phase 2
- Within US1: 11 recipe documentation tasks can run in parallel
- Within US2: 7 troubleshooting scenarios can run in parallel
- Within US3: 7 decision tree tasks can run in parallel

## MVP Scope

**Suggested MVP**: User Story 1 only (T006-T018)
- Delivers core value: all just recipes documented with examples
- 13 tasks, independently testable
- Operators can discover and use just recipes without reading source code

## Format Validation

✅ All tasks follow checklist format: `- [ ] T### [P?] [Story?] Description with file path`
✅ Task IDs are sequential (T001-T039)
✅ Story labels applied to all user story phase tasks (US1, US2, US3)
✅ Setup, Foundational, and Polish phases have no story labels
✅ File paths included in task descriptions (OPERATIONS.md, justfile, AGENTS.md)
✅ Parallel markers [P] applied to appropriate independent tasks
