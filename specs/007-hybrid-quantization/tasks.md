---
description: "Task list for per-path hybrid quantization feature"
---

# Tasks: Per-Path Hybrid Quantization

**Input**: Design documents from `/specs/007-hybrid-quantization/`
**Prerequisites**: plan.md, spec.md (user stories P1-P3), research.md, data-model.md, contracts/quantization-interface.md

**Tests**: Tests are NOT included (not explicitly requested in feature specification)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Single infrastructure project: `scripts/`, `tests/` at repository root
- Quantization profiles: `scripts/wrapper-config/profiles.yaml`
- Just recipes: `justfile`
- Health endpoint: `scripts/server-lifecycle.py`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Extend existing project structure with quantization support

- [x] T001 Extend `scripts/wrapper-config/profiles.yaml` with quantization_profiles schema (tq3a-tq2e-g32, tq4a-tq4e-g32 presets)
- [x] T002 [P] Create `scripts/quantization/` directory for quantization modules
- [x] T003 [P] Create `scripts/quantization/__init__.py` with module initialization
- [x] T004 Update `scripts/wrapper-config/presets.yaml` with quantization preset references (if needed)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Implement `scripts/quantization/profile_validator.py` with QuantizationProfile validation (bit-width 2-8, group_size validation, ERR-001/ERR-006 handling)
- [x] T006 [P] Implement `scripts/quantization/model_detector.py` with ModelArchitecture detection (layer type identification, MoE detection, expert count extraction)
- [x] T007 Implement `scripts/quantization/config_builder.py` to generate MLX quantization config from QuantizationProfile YAML
- [x] T008 Extend `scripts/server-lifecycle.py` health endpoint with `quantization` object (profile, attention_bits, expert_bits, group_size, model_architecture, is_moe, expert_count, active_params, total_params)
- [x] T009 Add `MLX_QUANT_PROFILE` environment variable support in `scripts/mlx_wrapper.py` or server startup logic
- [x] T010 Implement `scripts/quantization/quantization_manager.py` to coordinate profile application during model load

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Configure Per-Path Hybrid Quantization (Priority: P1) 🎯 MVP

**Goal**: Enable per-path hybrid quantization configuration (tq3a-tq2e g32) so system operators can optimize memory usage for 120B+ models on Apple Silicon.

**Independent Test**: Configure a model with `tq3a-tq2e g32` quantization settings and verify the model loads with correct bit allocation per path (attention layers at 3-bit, expert layers at 2-bit, group size 32). Verify health endpoint reports correct quantization configuration.

### Implementation for User Story 1

- [x] T011 [P] [US1] Implement `just quant-list` recipe in `justfile` to list available quantization profiles from `scripts/wrapper-config/profiles.yaml`
- [x] T012 [P] [US1] Implement `just quant-validate <profile>` recipe in `justfile` to validate quantization profile YAML (syntax, bit-width range, group_size) with exit codes 0/1
- [x] T013 [US1] Implement `just quant-apply <model> <profile>` recipe in `justfile` to apply quantization profile (validate, detect architecture, apply per-path quantization, update `.active-model`)
- [x] T014 [US1] Implement `just quant-status` recipe in `justfile` to display current quantization status for active model
- [x] T015 [US1] Extend `scripts/model-management.py` with `--quant-profile` parameter to accept quantization profile during model load
- [x] T016 [US1] Implement per-path quantization logic in `scripts/quantization/quantization_manager.py` to apply different bit-widths for attention vs expert layers using MLX `--quant-config`
- [x] T017 [US1] Add model checksum validation in `scripts/quantization/quantization_manager.py` before applying quantization (NFR-001, ERR-004)
- [x] T018 [US1] Add rollback logic in `scripts/quantization/quantization_manager.py` to revert to previous config on failed quantization (NFR-005)
- [x] T019 [US1] Add logging for quantization operations in `scripts/quantization/quantization_manager.py` (NFR-006)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Can configure and apply tq3a-tq2e g32 preset.

---

## Phase 4: User Story 2 - Support Latent-MoE Architectures (Priority: P2)

**Goal**: Enable quantization system to properly handle mixture-of-experts layer structures (Nemotron-3-Super-120B-A12B) so these models can be served efficiently on memory-constrained Apple Silicon systems.

**Independent Test**: Load a Nemotron-3-Super-120B-A12B model and verify that expert layers are correctly identified and quantized according to per-path configuration (3-bit attention, 2-bit expert).

### Implementation for User Story 2

- [x] T020 [P] [US2] Extend `scripts/quantization/model_detector.py` with latent-MoE detection for Nemotron-3-Super-120B-A12B using regex patterns (`.*nemotron.*120b.*`, `.*120b.*moe.*`)
- [x] T021 [US2] Implement expert layer identification in `scripts/quantization/model_detector.py` using layer name patterns (`.*expert.*`, `.*router.*`, `.*moe.*`)
- [x] T022 [US2] Add expert count extraction in `scripts/quantization/model_detector.py` from model config (`num_experts`, `n_experts` fields)
- [x] T023 [US2] Implement active parameter calculation in `scripts/quantization/model_detector.py` for MoE models (e.g., 12B for A12B models)
- [x] T024 [US2] Extend `scripts/quantization/quantization_manager.py` to apply expert-specific quantization settings for MoE architectures
- [x] T025 [US2] Add sparse expert activation handling in `scripts/quantization/quantization_manager.py` to load only active experts with correct quantization
- [x] T026 [US2] Update health endpoint in `scripts/server-lifecycle.py` with MoE-specific fields (`is_moe`, `expert_count`, `active_params`)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Latent-MoE architectures can be quantized with per-path configuration.

---

## Phase 5: User Story 3 - Configure Lloyd-Max Codebook Calibration (Priority: P3)

**Goal**: Enable Lloyd-Max codebook calibration with calibration data so system operators can achieve better quantization accuracy compared to standard quantization methods.

**Independent Test**: Provide calibration data and verify that the system generates optimized Lloyd-Max codebooks that improve quantization accuracy metrics. Verify V3 algorithm from sharpner/turboquant-mlx is correctly implemented.

### Implementation for User Story 3

- [x] T027 [P] [US3] Create `scripts/quantization/lloyd_max.py` with V3 Lloyd-Max algorithm implementation referencing sharpner/turboquant-mlx
- [x] T028 [US3] Implement calibration data loader in `scripts/quantization/lloyd_max.py` supporting JSON (tokenized text arrays), numpy (`.npy` files), and text formats (ERR-003 handling)
- [x] T029 [US3] Implement codebook generator in `scripts/quantization/lloyd_max.py` to create optimized lookup tables for different bit-widths and group sizes
- [x] T030 [US3] Add codebook serialization in `scripts/quantization/lloyd_max.py` to save `.mlx` files to `scripts/wrapper-config/codebooks/{codebook_id}.mlx`
- [x] T031 [US3] Implement `just quant-calibrate <dataset> <output>` recipe in `justfile` to run Lloyd-Max calibration with provided dataset
- [x] T032 [US3] Add calibration data path validation in `scripts/quantization/profile_validator.py` (secure path handling, NFR-002)
- [x] T033 [US3] Extend `scripts/quantization/quantization_manager.py` to integrate Lloyd-Max codebooks during quantization when `calibration_method: "lloyd-max"`
- [x] T034 [US3] Add perplexity improvement measurement in `scripts/quantization/lloyd_max.py` to compare Lloyd-Max vs standard quantization

**Checkpoint**: All user stories should now be independently functional. Lloyd-Max codebook calibration is available for quality optimization.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T035 [P] Update `OPERATIONS.md` with quantization recipes documentation (quant-apply, quant-validate, quant-list, quant-calibrate, quant-status)
- [x] T036 [P] Update `README.md` with per-path hybrid quantization feature overview and quickstart reference
- [x] T037 Add error handling for ERR-001 through ERR-006 in all quantization modules with proper HTTP status codes (400, 422, 507)
- [x] T038 Add integration test for complete flow in `tests/test_quantization_integration.py` (profile apply → model load → health check → inference)
- [x] T039 Validate quickstart.md scenarios end-to-end (Steps 1-7) to ensure all user journeys work correctly
- [x] T040 Code cleanup and refactoring across `scripts/quantization/` modules
- [x] T041 Add security validation for calibration data file paths to prevent path traversal (NFR-002)
- [x] T042 Verify OpenAI-compatible API behavior is preserved when serving models with hybrid quantization (FR-009)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Models before services (data-model.md entities → quantization modules)
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
# Launch all parallel tasks for User Story 1 together:
Task: "Implement just quant-list recipe in justfile"
Task: "Implement just quant-validate <profile> recipe in justfile"
```

```bash
# Launch all implementation tasks for User Story 1:
Task: "Extend scripts/model-management.py with --quant-profile parameter"
Task: "Implement per-path quantization logic in scripts/quantization/quantization_manager.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T010) - CRITICAL: blocks all stories
3. Complete Phase 3: User Story 1 (T011-T019)
4. **STOP and VALIDATE**: Test User Story 1 independently
   - Apply tq3a-tq2e g32 preset to a model
   - Verify health endpoint shows correct quantization config
   - Confirm model loads with 3-bit attention, 2-bit expert, group 32
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
   - Developer A: User Story 1 (T011-T019)
   - Developer B: User Story 2 (T020-T026)
   - Developer C: User Story 3 (T027-T034)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (if tests were requested)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Task Summary

- **Total Tasks**: 42
- **Completed**: 42 ✓
- **Remaining**: 0
- **Phase 1 (Setup)**: 4/4 complete ✓
- **Phase 2 (Foundational)**: 6/6 complete ✓
- **Phase 3 (US1 - P1)**: 9/9 complete ✓
- **Phase 4 (US2 - P2)**: 7/7 complete ✓
- **Phase 5 (US3 - P3)**: 8/8 complete ✓
- **Phase 6 (Polish)**: 8/8 complete ✓

### Parallel Opportunities

- 14 tasks marked [P] can run in parallel (T002, T003, T006, T011, T012, T020, T027, T035, T036)
- User Stories 1, 2, 3 can run in parallel after Phase 2 completion

### Independent Test Criteria

- **US1**: Configure tq3a-tq2e g32, load model, verify 3-bit attention/2-bit expert in health endpoint ✓
- **US2**: Load Nemotron-3-Super-120B-A12B, verify expert layer detection and quantization ✓
- **US3**: Provide calibration data, generate Lloyd-Max codebooks, verify perplexity improvement ✓

### Suggested MVP Scope

**MVP = User Story 1 Only (Phase 3)**
- Core per-path hybrid quantization with tq3a-tq2e g32 preset
- just recipes: quant-list, quant-validate, quant-apply, quant-status
- Health endpoint quantization reporting
- Model checksum validation and rollback
- Enables 120B+ models on 48GB Apple Silicon systems
