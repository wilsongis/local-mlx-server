---
description: "Task list for KV Cache Compression feature"
---

# Tasks: KV Cache Compression

**Input**: Design documents from `/specs/008-kv-cache-compression/`

**Prerequisites**: plan.md, spec.md, data-model.md, contracts/kv-cache-interface.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- Python source: `scripts/quantization/`
- Configuration: `scripts/wrapper-config/`
- Server lifecycle: `scripts/server-lifecycle.py`
- Operations: `justfile`
- Documentation: `docs/`, `OPERATIONS.md`, `README.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing infrastructure and prepare for KV cache compression integration

- [x] T001 Review existing quantization infrastructure in scripts/quantization/ and scripts/wrapper-config/
- [x] T002 [P] Verify TurboQuant MLX package availability (turboquant-mlx-full) in pyproject.toml
- [x] T003 [P] Confirm Metal kernel compilation tools (Xcode CLI, CMake) are available

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create CompressionProfile data class in scripts/quantization/kv_cache_profiles.py
- [x] T005 Create ModelSizeClass enumeration in scripts/quantization/kv_cache_profiles.py
- [x] T006 Create AttentionCacheType enumeration in scripts/quantization/kv_cache_compression.py
- [x] T007 Implement KVCacheCompressionManager class skeleton in scripts/quantization/kv_cache_compression.py
- [x] T008 Implement convert_cache_to_turboquant() function in scripts/quantization/kv_cache_compression.py
- [x] T009 Extend config_builder.py to parse kv_cache configuration from profiles.yaml in scripts/quantization/config_builder.py
- [x] T010 Create kv_cache_profiles.yaml with v2-speed, v3-quality, and auto profiles in scripts/wrapper-config/kv-cache-profiles.yaml
- [x] T011 Modify quantization_manager.py to initialize KVCacheCompressionManager in scripts/quantization/quantization_manager.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Run Larger Models with Less Memory (Priority: P1) 🎯 MVP

**Goal**: Enable 120B+ parameter models on 48GB Apple Silicon systems by reducing KV cache memory usage by 3-5x

**Independent Test**: Measure memory usage before and after enabling KV cache compression with a fixed model and context length, verifying memory reduction by expected compression ratio while maintaining output quality within 2% of baseline.

### Implementation for User Story 1

- [x] T012 [US1] Integrate KVCacheCompressionManager with QuantizationManager.apply_kv_cache_compression() in scripts/quantization/quantization_manager.py
- [x] T013 [US1] Modify server-lifecycle.py to call convert_cache_to_turboquant() after prompt processing in scripts/server-lifecycle.py
- [x] T014 [US1] Add compression status reporting to health endpoint via KVCacheCompressionManager.get_status() in scripts/server-lifecycle.py
- [x] T015 [US1] Update justfile with kv-status recipe to display current compression status in justfile
- [x] T016 [US1] Update justfile with kv-enable recipe accepting PROFILE and BITS parameters in justfile
- [x] T017 [US1] Update justfile with kv-disable recipe to disable compression in justfile
- [x] T018 [US1] Add fallback to uncompressed KVCache on initialization failure in scripts/quantization/kv_cache_compression.py
- [x] T019 [US1] Detect AttentionCacheType and skip compression for RotatingKVCache/ArraysCache in scripts/quantization/kv_cache_compression.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently - KV cache compression reduces memory usage by 3-5x for 120B+ models.

---

## Phase 4: User Story 2 - Choose Speed-Optimized Compression (Priority: P2)

**Goal**: Provide a speed-optimized compression path (V2) using Metal-accelerated operations to achieve ~3.6x compression while maintaining ~105% of FP16 inference speed

**Independent Test**: Enable speed-optimized compression path and measure tokens-per-second throughput compared to uncompressed baseline, verifying it meets or exceeds FP16 speed with 3x+ memory reduction.

### Implementation for User Story 2

- [x] T020 [P] [US2] Implement V2 speed-optimized path with mx.quantized_matmul Metal acceleration in scripts/quantization/kv_cache_compression.py
- [x] T021 [US2] Configure V2 profile with codebook_type="uniform", use_metal=true in scripts/quantization/kv_cache_profiles.py
- [x] T022 [US2] Add hadamard_rotation=true for quality preservation in V2 profile in scripts/quantization/kv_cache_profiles.py
- [ ] T023 [US2] Validate V2 path achieves ≥100% FP16 speed with 3x+ compression in scripts/quantization/kv_cache_compression.py
- [ ] T024 [US2] Ensure Metal accelerator is utilized for quantization operations without CPU fallback in scripts/quantization/kv_cache_compression.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - users can choose speed-optimized compression.

---

## Phase 5: User Story 3 - Choose Quality-Optimized Compression (Priority: P2)

**Goal**: Provide a quality-optimized compression path (V3) using Lloyd-Max codebook to achieve 4.1-5.5x compression with minimal quality loss, ideal for maximum memory reduction

**Independent Test**: Enable quality-optimized compression path and verify compression ratios of 4x+ are achieved while quality remains within 2% of FP16 baseline on standard benchmarks.

### Implementation for User Story 3

- [x] T025 [P] [US3] Implement V3 quality-optimized path with Lloyd-Max codebook in scripts/quantization/kv_cache_compression.py
- [x] T026 [US3] Configure V3 profile with codebook_type="lloyd-max", use_metal=true in scripts/quantization/kv_cache_profiles.py
- [x] T027 [US3] Implement custom Metal kernel loading for V3 path with CPU fallback in scripts/quantization/kv_cache_compression.py
- [x] T028 [US3] Add Lloyd-Max codebook computation from data when precomputed unavailable in scripts/quantization/kv_cache_compression.py
- [ ] T029 [US3] Validate V3 path achieves 4x+ compression with <2% quality loss vs FP16 in scripts/quantization/kv_cache_compression.py

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently - users can choose between speed and quality compression paths.

---

## Phase 6: User Story 4 - Automatic Compression Strategy Selection (Priority: P3)

**Goal**: Automatically select optimal compression strategy based on model size class, applying double-compression rules (3-bit weights + 4-bit KV for ~20B, 3-bit+3-bit for 100B+)

**Independent Test**: Load models of different sizes and verify system automatically selects and applies appropriate compression strategy for each model size class without manual reconfiguration.

### Implementation for User Story 4

- [x] T030 [US4] Implement select_profile() logic based on ModelSizeClass and weight_bits in scripts/quantization/kv_cache_compression.py
- [x] T031 [US4] Add double-compression rules: 3-bit weights + 4-bit KV for 20B, 3-bit+3-bit for 100B+ in scripts/quantization/kv_cache_compression.py
- [x] T032 [US4] Implement auto profile detection of model size from loaded model in scripts/quantization/kv_cache_compression.py
- [x] T033 [US4] Add model change handler to re-evaluate compression strategy in scripts/quantization/kv_cache_compression.py
- [x] T034 [US4] Test auto profile selects correct strategy for ~20B models (3-bit weights + 4-bit KV) in tests/test_kv_cache_auto.py
- [x] T035 [US4] Test auto profile selects correct strategy for 100B+ models (3-bit weights + 3-bit KV) in tests/test_kv_cache_auto.py

**Checkpoint**: All user stories should now be independently functional - system automatically optimizes compression based on model size.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T036 [P] Update OPERATIONS.md with KV cache compression section including just recipes in OPERATIONS.md
- [x] T037 [P] Update README.md with KV cache compression feature description in README.md
- [x] T038 [P] Update scripts/wrapper-config/profiles.yaml with example kv_cache configuration in scripts/wrapper-config/profiles.yaml
- [x] T039 Add comprehensive error handling and logging for all compression paths in scripts/quantization/kv_cache_compression.py
- [x] T040 Validate compression works with all attention cache types (KVCache ✓, RotatingKVCache ✗, ArraysCache ✗) in scripts/quantization/kv_cache_compression.py
- [x] T041 Add compression mode switching without server restart via convert_cache_to_turboquant() in scripts/quantization/kv_cache_compression.py
- [x] T042 Run quickstart.md validation scenarios end-to-end from specs/008-kv-cache-compression/quickstart.md
- [x] T043 Update GOVERNANCE.md if compression affects project constitution boundaries in GOVERNANCE.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories - **MVP**
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent, may integrate with US1 components
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Independent, may integrate with US1/US2 components
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Independent, builds on US1 foundation

### Within Each User Story

- Foundational tasks before user story tasks
- Profile configuration before compression implementation
- Core implementation before validation/testing
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- V2 and V3 path implementations (US2, US3) can run in parallel
- All documentation tasks marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all implementation tasks for User Story 1 together:
Task: "Integrate KVCacheCompressionManager with QuantizationManager in scripts/quantization/quantization_manager.py"
Task: "Modify server-lifecycle.py to call convert_cache_to_turboquant() after prompt processing"
Task: "Add compression status reporting to health endpoint"
Task: "Update justfile with kv-status, kv-enable, kv-disable recipes"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Run Larger Models with Less Memory)
4. **STOP and VALIDATE**: Test User Story 1 independently - verify 120B+ models run on 48GB with 3-5x KV cache memory reduction
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (Speed-Optimized) → Test independently → Deploy/Demo
4. Add User Story 3 (Quality-Optimized) → Test independently → Deploy/Demo
5. Add User Story 4 (Auto-Selection) → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (MVP)
   - Developer B: User Story 2 (Speed-Optimized)
   - Developer C: User Story 3 (Quality-Optimized)
   - Developer D: User Story 4 (Auto-Selection)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify compression mode switching works without server restart
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- All compression paths must fallback gracefully to uncompressed on failure (FR-010)
- Double-compression tolerance rules must be strictly followed (3-bit weights + 4-bit KV for 20B, 3-bit+3-bit for 100B+)

---

**Total Tasks**: 43
**Completed**: 35
**Remaining**: 8

**Tasks per User Story**:
- US1 (P1): 8 tasks (T012-T019) - COMPLETE ✓
- US2 (P2): 5 tasks (T020-T024) - 3 complete, 2 remaining
- US3 (P2): 5 tasks (T025-T029) - 4 complete, 1 remaining
- US4 (P3): 6 tasks (T030-T035) - 4 complete, 2 remaining

**Parallel Opportunities**: 12 tasks marked [P] for parallel execution

**MVP Scope**: User Story 1 only (T012-T019) - COMPLETE ✓ - enables 120B+ models on 48GB systems with 3-5x KV cache memory reduction
