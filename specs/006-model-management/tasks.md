---
description: "Task list for Model Management feature implementation"
---

# Tasks: Model Management

**Input**: Design documents from `/specs/006-model-management/` (plan.md, spec.md, data-model.md, contracts/, quickstart.md, research.md)

**Prerequisites**: Python 3.11+, pyyaml, psutil, existing justfile infrastructure

**Tests**: Tests are OPTIONAL - include test tasks as requested. This feature does not explicitly request TDD approach, so test tasks are included as optional validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Python scripts: `scripts/`
- Configuration: `scripts/wrapper-config/`
- Tests: `tests/`
- Just recipes: `justfile`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure verification

- [ ] T001 Verify Python 3.11+ environment and install dependencies (pyyaml, psutil) via uv/pip
- [ ] T002 [P] Verify existing justfile structure and scripts directory exists
- [ ] T003 [P] Create `scripts/model-management.py` with module docstring and imports (pyyaml, os, pathlib, json, fcntl for flock)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Define `ModelProfile` dataclass/structure in `scripts/model-management.py` with fields: name, model_path, description, memory_estimate_gb, quantization, kv_cache, inference_args
- [ ] T005 Define `ValidationResult` dataclass in `scripts/model-management.py` with fields: profile_name, is_valid, errors, warnings, path_exists, key_files_present, missing_files, disk_space_gb_available, disk_space_gb_required, validation_timestamp
- [ ] T006 Implement `ModelRegistry` class in `scripts/model-management.py` with initialization that reads `scripts/wrapper-config/profiles.yaml`
- [ ] T007 Implement `list_profiles()` method in `ModelRegistry` class in `scripts/model-management.py`
- [ ] T008 Implement `get_profile(name: str)` method in `ModelRegistry` class in `scripts/model-management.py`
- [ ] T009 Create state file management functions in `scripts/model-management.py`: `get_active_profile()` and `set_active_profile(name: str)` with flock locking
- [ ] T010 [P] Create initial `scripts/wrapper-config/profiles.yaml` with three model profiles: nemotron-120b, gpt-oss-120b, qwen3.5-122b with required fields

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - List Available Model Profiles (Priority: P1) 🎯 MVP

**Goal**: As a server operator, I want to list all available model profiles so that I can see which large language models are configured and available for serving.

**Independent Test**: Can be fully tested by running `just models-list` and verifying it returns all configured model profiles with their key metadata (name, path, size requirements).

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `list_models_cli()` function in `scripts/model-management.py` that formats human-readable output with profile metadata
- [ ] T012 [P] [US1] Implement JSON output option in `list_models_cli()` function in `scripts/model-management.py` for `--json` flag
- [ ] T013 [US1] Add `models-list` recipe to `justfile` that calls `python scripts/model-management.py list` with optional `--json` flag
- [ ] T014 [US1] Implement active profile detection in `list_models_cli()` in `scripts/model-management.py` to show which profile is currently active
- [ ] T015 [US1] Add error handling in `scripts/model-management.py` for missing or malformed `profiles.yaml` with clear error message
- [ ] T016 [US1] Update `scripts/model-management.py` main block to handle `list` command with argument parsing (argparse)

**Checkpoint**: At this point, User Story 1 should be fully functional - `just models-list` works and shows all profiles with metadata.

---

## Phase 4: User Story 2 - Select and Activate Model Profile (Priority: P1)

**Goal**: As a server operator, I want to select a specific model profile for serving so that I can switch between different large language models based on my current inference needs.

**Independent Test**: Can be fully tested by running `just model-use <profile>` and verifying the system acknowledges the selection and writes to state file.

### Implementation for User Story 2

- [ ] T017 [P] [US2] Implement `validate_profile_exists()` in `ModelRegistry` class in `scripts/model-management.py` to check if profile name exists in registry
- [ ] T018 [US2] Implement `activate_model_cli(profile_name: str, validate: bool, force: bool)` function in `scripts/model-management.py`
- [ ] T019 [US2] Add validation skip logic in `activate_model_cli()` in `scripts/model-management.py` based on `--validate` and `--force` flags
- [ ] T020 [US2] Add `model-use` recipe to `justfile` that calls `python scripts/model-management.py use <profile>` with optional `--validate` and `--force` flags
- [ ] T021 [US2] Implement profile not found error handling in `scripts/model-management.py` with list of available profiles in error message
- [ ] T022 [US2] Add `model-status` recipe to `justfile` that shows currently active profile (reads `.active-model` state file)
- [ ] T023 [US2] Update `scripts/model-management.py` main block to handle `use` command and `status` command with argument parsing

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - users can list and select model profiles.

---

## Phase 5: User Story 3 - Validate Model Path and Disk Space (Priority: P2)

**Goal**: As a server operator, I want the system to automatically validate that model files exist at the configured path and that sufficient disk space is available so that I can avoid runtime failures.

**Independent Test**: Can be fully tested by configuring a model with various path and disk space conditions and verifying appropriate validation messages.

### Implementation for User Story 3

- [ ] T024 [P] [US3] Implement `validate_model_path(profile: ModelProfile)` in `scripts/model-management.py` to check if model_path exists and expand ~
- [ ] T025 [P] [US3] Implement `check_key_files(profile: ModelProfile)` in `scripts/model-management.py` to verify config.json and weight files (*.safetensors, *.npz) exist
- [ ] T026 [US3] Implement `check_disk_space(profile: ModelProfile)` in `scripts/model-management.py` using psutil to compare available space vs memory_estimate_gb
- [ ] T027 [US3] Implement `validate_profile(name: str) -> ValidationResult` method in `ModelRegistry` class in `scripts/model-management.py` that runs all validation checks
- [ ] T028 [US3] Integrate validation into `activate_model_cli()` in `scripts/model-management.py` to run before activation (unless `--force` is used)
- [ ] T029 [US3] Format validation output in `scripts/model-management.py` to show ✓/✗ for each check with details (path, files, disk space)
- [ ] T030 [US3] Add validation-only mode to `just model-use` that runs validation without activating (if `--validate-only` flag is needed)

**Checkpoint**: All user stories should now be independently functional - listing, selecting, and validating models all work.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements, integration, and ensuring all pieces work together

- [ ] T031 [P] Add comprehensive error messages throughout `scripts/model-management.py` with actionable suggestions (e.g., "Run 'just models-list' to see available profiles")
- [ ] T032 [P] Add logging to `scripts/model-management.py` using Python logging module for debugging and audit trail
- [ ] T033 Update `OPERATIONS.md` to document new `just models-list`, `just model-use`, and `just model-status` commands with examples
- [ ] T034 Update `README.md` if needed to mention model management capabilities
- [ ] T035 Integrate model management with existing server lifecycle in `scripts/server-lifecycle.py` to read active model from `.active-model`
- [ ] T036 Add `model-status` check to `just mlx-start` recipe to warn if no model is active before server startup
- [ ] T037 Test concurrent model profile changes by running simultaneous `just model-use` commands and verifying flock locking works
- [ ] T038 Verify all three target model profiles (Nemotron-120B-48GB, GPT-OSS-120B, Qwen3.5-122B) are properly configured in `scripts/wrapper-config/profiles.yaml`

---

## Dependencies Section

### User Story Completion Order

```
Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1: List Models) → Phase 4 (US2: Select Model) → Phase 5 (US3: Validate Model) → Phase 6 (Polish)
```

### Story Dependencies

- **US1 (List Models)**: Depends on Phase 2 foundational tasks (T004-T010). Can be tested independently after Phase 2.
- **US2 (Select Model)**: Depends on Phase 2 foundational tasks (T004-T010) and US1 for listing available profiles. Can be tested independently after Phase 2.
- **US3 (Validate Model)**: Depends on Phase 2 foundational tasks (T004-T010). Integrates with US2 but can be tested independently.

### Parallel Execution Examples

**After Phase 2 Complete - Can run in parallel:**
```bash
# Terminal 1: Work on US1
# Implement T011, T012, T013 in parallel (different concerns)

# Terminal 2: Work on US3 validation functions
# Implement T024, T025, T026 in parallel (different validation aspects)
```

**Within US1 - Parallel tasks:**
- T011 and T012 can run in parallel (different output formats)
- T013 can run in parallel with T011/T012 (different file: justfile vs model-management.py)

**Within US2 - Parallel tasks:**
- T017 can run in parallel with US1 tasks (foundational method)
- T020 can run in parallel with T017 (justfile vs model-management.py)

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)
**Suggested MVP = User Story 1 + User Story 2** (both P1 priority)
- `just models-list` - List all available model profiles
- `just model-use <profile>` - Select and activate a model profile
- Basic validation (profile exists check)

This MVP delivers core value: discovering and selecting models for serving.

### Incremental Delivery Plan

1. **Phase 1-2**: Setup and foundational infrastructure (blocking for all stories)
2. **Phase 3 (US1)**: Deliver `just models-list` - immediately useful for operators
3. **Phase 4 (US2)**: Deliver `just model-use` and `just model-status` - complete the core workflow
4. **Phase 5 (US3)**: Add validation - hardens the system against runtime failures
5. **Phase 6**: Polish and integration - ensures production readiness

### Testing Strategy
Tests are OPTIONAL for this feature. If tests are requested later:
- Unit tests for `ModelRegistry` methods in `tests/test_model_management.py`
- Integration tests for `just` recipes
- Validation tests for various path/disk space scenarios

---

## Task Summary

- **Total Tasks**: 38
- **User Story 1 (US1)**: 6 tasks (T011-T016)
- **User Story 2 (US2)**: 7 tasks (T017-T023)
- **User Story 3 (US3)**: 7 tasks (T024-T030)
- **Setup & Foundational**: 10 tasks (T001-T010)
- **Polish & Cross-Cutting**: 8 tasks (T031-T038)
- **Parallelizable Tasks [P]**: 14 tasks

### Format Validation
✅ All tasks follow the checklist format: `- [ ] T### [P?] [Story?] Description with file path`
✅ All user story phase tasks include [Story] label
✅ Setup, Foundational, and Polish phases do NOT have [Story] labels
✅ File paths are included in task descriptions
✅ Task IDs are sequential (T001-T038)

---

**Generated**: 2026-05-20
**Feature**: Model Management (006-model-management)
**Next Step**: Run `/speckit.implement` to begin implementation starting with Phase 1 tasks.
