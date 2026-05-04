---
description: "Task list for Documentation Consolidation feature"
---

# Tasks: Documentation Consolidation

**Input**: Design documents from `/specs/001-documentation-consolidation/`
**Prerequisites**: 
- Source content files: README.md, AGENTS.md, `.specify/memory/constitution.md`
- Design artifacts: plan.md, spec.md, data-model.md, research.md, quickstart.md (inform implementation but are NOT source content for consolidation)

**Tests**: Tests are NOT included (not requested in feature specification - this is documentation-only)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare for documentation consolidation

- [x] T001 Read and analyze current README.md to identify all content sections
- [x] T002 Read and analyze current AGENTS.md to identify all content sections
- [x] T003 Read and analyze `.specify/memory/constitution.md` to identify all content sections
- [x] T004 [P] Create content mapping document mapping original content to target files (README.md, OPERATIONS.md, AGENTS.md, GOVERNANCE.md, CONTRIBUTING.md)
- [x] T005 [P] Prepare content audit checklist for verifying 100% content preservation (Success Criterion SC-001) based on Critical Information Definition in spec.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core content mapping that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Create content mapping matrix: README.md → README.md (index) + OPERATIONS.md (operations content)
- [x] T007 Create content mapping matrix: AGENTS.md → AGENTS.md (agent rules) + GOVERNANCE.md (governance content)
- [x] T008 Create content mapping matrix: constitution.md → GOVERNANCE.md (all governance principles)
- [x] T009 Define documentation standards outline for GOVERNANCE.md (6+ sections per SC-003, explicitly listed in FR-003)
- [x] T010 Define persona-specific navigation structure for README.md index (Operators, Contributors, Maintainers per SC-006)
- [x] T011 Define markdown formatting standards (FR-007): heading levels, code block syntax, table formatting, link style for all documentation files

**Checkpoint**: Content mapping complete - user story implementation can now begin

---

## Phase 3: User Story 1 - Unified Documentation Structure (Priority: P1) 🎯 MVP

**Goal**: Create a well-organized multi-file documentation structure with README.md as the central index, linking to OPERATIONS.md, AGENTS.md, GOVERNANCE.md, and CONTRIBUTING.md.

**Independent Test**: Can be fully tested by navigating the documentation structure and verifying all critical information from README.md, AGENTS.md, and constitution is present and accessible across the multi-file structure.

### Implementation for User Story 1

- [x] T012 [P] [US1] Create/Update README.md as central index with persona-specific navigation in README.md
- [x] T013 [P] [US1] Create OPERATIONS.md with server operations and just recipes from original README.md in OPERATIONS.md
- [x] T014 [P] [US1] Update AGENTS.md preserving agent rules and operational charter from original AGENTS.md in AGENTS.md
- [x] T015 [US1] Create GOVERNANCE.md combining constitution.md content and governance sections from AGENTS.md in GOVERNANCE.md
- [x] T016 [US1] Create CONTRIBUTING.md with contribution guidelines and development workflow in CONTRIBUTING.md (NEW file - not from original sources)
- [x] T017 [US1] Add cross-references between README.md, OPERATIONS.md, AGENTS.md, GOVERNANCE.md, and CONTRIBUTING.md (minimum 2 per file per FR-008)
- [x] T018 [US1] Perform content audit: Verify 100% of critical content from original README.md preserved in README.md and OPERATIONS.md
- [x] T019 [US1] Perform content audit: Verify 100% of critical content from original AGENTS.md preserved in AGENTS.md and GOVERNANCE.md
- [x] T020 [US1] Perform content audit: Verify 100% of critical content from constitution.md preserved in GOVERNANCE.md

**Checkpoint**: At this point, User Story 1 should be fully functional - all 5 files exist with consolidated content

---

## Phase 4: User Story 2 - Documentation Standards Definition (Priority: P2)

**Goal**: Define clearly documented standards in GOVERNANCE.md that specify how inference infrastructure projects should document their architecture, operations, and agent rules.

**Independent Test**: Can be fully tested by reviewing the standards document against actual project documentation and verifying all required elements are covered.

### Implementation for User Story 2

- [x] T021 [P] [US2] Define overview/purpose standards section in GOVERNANCE.md
- [x] T022 [P] [US2] Define installation/setup standards section in GOVERNANCE.md
- [x] T023 [P] [US2] Define operations standards section (just recipes, server startup, troubleshooting) in GOVERNANCE.md
- [x] T024 [P] [US2] Define agent rules standards section (AGENTS.md structure, operational charter) in GOVERNANCE.md
- [x] T025 [US2] Define governance standards section (constitution, documentation standards, release processes) in GOVERNANCE.md
- [x] T026 [P] [US2] Define contribution standards section (PR workflow, testing, code style) in GOVERNANCE.md
- [x] T027 [US2] Add inference-specific standards: model serving endpoints documentation requirements in GOVERNANCE.md
- [x] T028 [US2] Add inference-specific standards: quantization/memory considerations documentation in GOVERNANCE.md
- [x] T029 [US2] Add inference-specific standards: Apple Silicon constraints documentation in GOVERNANCE.md
- [x] T030 [US2] Add inference-specific standards: mlx_lm.server compatibility documentation in GOVERNANCE.md
- [x] T031 [US2] Verify GOVERNANCE.md has at least 6 core sections (SC-003)
- [x] T032 [US2] Verify documentation standards are reusable for other inference infrastructure projects (SC-005)

**Checkpoint**: At this point, User Stories 1 AND 2 should both be complete - documentation structure exists with defined standards

---

## Phase 5: User Story 3 - Navigation and Discoverability (Priority: P3)

**Goal**: Ensure users can quickly find specific information through clear navigation in README.md index and cross-references between all documentation files.

**Independent Test**: Can be fully tested by timing how long it takes a new user to find specific pieces of information using only the documentation structure. **Measurement Method**: Self-test by unfamiliar person using only documentation, timed with stopwatch (max 2 minutes per information type).

### Implementation for User Story 3

- [x] T0*33 [US3] Enhance README.md index with table of contents organized by persona needs (FR-005, SC-006)
- [x] T0*34 [US3] Add Operator-specific quick links section in README.md (server startup, just recipes)
- [x] T0*35 [US3] Add Contributor-specific quick links section in README.md (setup, AGENTS.md, contributing)
- [x] T0*36 [US3] Add Maintainer-specific quick links section in README.md (governance, constitution)
- [x] T0*37 [P] [US3] Audit and improve cross-references in OPERATIONS.md (minimum 2 per file)
- [x] T0*38 [P] [US3] Audit and improve cross-references in AGENTS.md (minimum 2 per file)
- [x] T0*39 [P] [US3] Audit and improve cross-references in GOVERNANCE.md (minimum 2 per file)
- [x] T0*40 [P] [US3] Audit and improve cross-references in CONTRIBUTING.md (minimum 2 per file)
- [x] T0*41 [US3] Add inline navigation hints in OPERATIONS.md for related topics
- [x] T0*42 [US3] Add inline navigation hints in AGENTS.md for related topics
- [x] T0*43 [US3] Add inline navigation hints in GOVERNANCE.md for related topics
- [x] T0*44 [US3] Add inline navigation hints in CONTRIBUTING.md for related topics
- [x] T0*45 [US3] Test Operator navigation: Verify server startup can be found within 2 minutes (SC-002)
- [x] T0*46 [US3] Test Contributor navigation: Verify agent rules can be found within 2 minutes (SC-002)
- [x] T0*47 [US3] Test Maintainer navigation: Verify governance info can be found within 2 minutes (SC-002)

**Checkpoint**: All user stories should now be complete - documentation structure, standards, and navigation all implemented

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T0*48 [P] Apply consistent markdown formatting across all 5 files per T011 standards (FR-007): README.md, OPERATIONS.md, AGENTS.md, GOVERNANCE.md, CONTRIBUTING.md
- [x] T0*49 [P] Run markdown linter on all documentation files
- [x] T0*50 Verify all success criteria (SC-001 through SC-006) are met
- [x] T0*51 Final content audit: Ensure no critical content lost from original files
- [x] T0*52 Validate all internal links work across documentation files
- [x] T0*53 Update TODO.md to reflect completed documentation consolidation
- [x] T0*54 Run quickstart.md validation steps to verify documentation works as expected

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories - **MVP**
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May reference US1 files but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 being complete (needs the files to exist for navigation testing)

### Within Each User Story

- Content creation before content audit
- Core files before cross-references
- Navigation features after base content exists
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T004, T005)
- All Foundational tasks can run in parallel (T006-T011)
- Once Foundational phase completes, US1 can start immediately
- US2 can start after Phase 2 (parallel with US1 if desired, but US1 is MVP)
- US3 should wait for US1 completion (needs files to exist)
- All cross-reference tasks in US3 marked [P] can run in parallel (T037-T040)
- All markdown formatting tasks in Polish phase marked [P] can run in parallel (T048, T049)

---

## Parallel Example: User Story 1

```bash
# These tasks can run in parallel (different files):
# Terminal 1:
echo "Creating README.md index..." && # T012 work

# Terminal 2:
echo "Creating OPERATIONS.md..." && # T013 work

# Terminal 3:
echo "Updating AGENTS.md..." && # T014 work

# Terminal 4:
echo "Creating GOVERNANCE.md..." && # T015 work

# Terminal 5:
echo "Creating CONTRIBUTING.md..." && # T016 work
```

---

## Summary

- **Total Tasks**: 54
- **User Story 1 (US1)**: 9 tasks (T012-T020)
- **User Story 2 (US2)**: 12 tasks (T021-T032)
- **User Story 3 (US3)**: 15 tasks (T033-T047)
- **Setup Phase**: 5 tasks (T001-T005)
- **Foundational Phase**: 6 tasks (T006-T011)
- **Polish Phase**: 7 tasks (T048-T054)

### Parallel Opportunities

- 18 tasks marked [P] can run in parallel where dependencies allow
- US1 tasks T012-T014 can all run in parallel (different files)
- US2 tasks T021-T024 can mostly run in parallel (different sections)
- US3 cross-reference tasks T037-T040 can run in parallel

### Independent Test Criteria

- **US1**: Navigate docs, verify all critical content present across 5 files
- **US2**: Review GOVERNANCE.md standards, verify 6+ sections with inference-specific content
- **US3**: Time-based navigation test - find info within 2 minutes per persona (measured with stopwatch)

### Suggested MVP Scope

**User Story 1 only** (T012-T020): Creates the unified documentation structure with all 5 files and verifies content preservation. This delivers immediate value - users can navigate the new documentation structure.

---

## Format Validation

✅ All tasks follow the checklist format:
- Starts with `- [ ]`
- Includes Task ID (T001, T002, etc.)
- Includes [P] marker where parallelizable
- Includes [Story] label for user story phases (US1, US2, US3)
- Includes description with file path

✅ Tasks are organized by user story for independent implementation and testing
