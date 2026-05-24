# Implementation Plan: KV Cache Compression

**Branch**: `feature/kv-cache-compression` | **Date**: 2026-05-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/008-kv-cache-compression/spec.md`

## Summary

Implement KV cache compression for MLX-based local inference to reduce memory usage by 3-5x on Apple Silicon systems. The feature introduces two selectable compression paths: speed-optimized (V2, Metal-accelerated, ~3.6x compression at ~105% FP16 speed) and quality-optimized (V3, Lloyd-Max codebook, 4.1-5.5x compression). Includes hybrid attention support (KVCache, RotatingKVCache, ArraysCache), automatic compression strategy selection based on model size, and double-compression configurations (combined weight + KV cache compression) for 120B+ model viability on 48GB systems.

## Technical Context

**Language/Version**: Python 3.11+ (consistent with existing codebase)

**Primary Dependencies**: 
- `mlx` and `mlx-lm` (existing, for inference and `mlx_lm.server`)
- TurboQuant V2/V3 implementations (reference: sharpner/turboquant-mlx, arozan/turboquant-mlx)
- Custom Metal kernels for V3 quality-optimized path
- Existing hybrid quantization infrastructure from spec 007

**Storage**: N/A (runtime memory optimization, no persistent storage changes)

**Testing**: pytest (existing framework, see `tests/` directory)

**Target Platform**: macOS/Apple Silicon (Metal acceleration required)

**Project Type**: Infrastructure/Server enhancement (extends `scripts/quantization/` and server startup workflows)

**Performance Goals**: 
- Speed-optimized path: ≥100% of uncompressed FP16 inference speed, 3.6x compression
- Quality-optimized path: 4.1-5.5x compression, output quality within 2% of FP16 baseline
- Compression mode switching: <5 seconds without server restart
- Enable 120B+ models on 48GB Apple Silicon systems

**Constraints**:
- Must preserve OpenAI-compatible API via `mlx_lm.server`
- Memory reduction must not degrade output quality beyond 2% (perplexity/task accuracy)
- Metal acceleration required for V2; V3 requires custom kernel compilation/loading
- Compatible with existing hybrid quantization (spec 007) for double-compression

**Scale/Scope**: 
- Affects KV cache handling in `scripts/quantization/` and server lifecycle
- 3 compression profiles (speed, quality, auto-select)
- 3 attention cache types supported (KVCache, RotatingKVCache, ArraysCache)
- Integration with `just` recipes for operational control

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Infrastructure-Only Scope** | ✅ PASS | Feature extends local inference infrastructure only; no product/web-stack code |
| **II. Local Serving Reliability** | ✅ PASS | Preserves `mlx_lm.server` OpenAI-compatible endpoint; adds compression as configurable option |
| **III. Quantization and Memory First** | ✅ PASS | Directly optimizes KV cache memory for 120B+ models on Apple Silicon; builds on spec 007 hybrid quantization |
| **IV. Just Command Bridge** | ⚠️ CHECK | Must add/extend `just` recipes for compression mode selection and status queries |
| **V. Reversible, Testable Changes** | ✅ PASS | Compression can be disabled (fallback to uncompressed); changes are incremental to `scripts/quantization/` |

**Gate Decision**: PASS (IV addressed during implementation by adding just recipes)

## Project Structure

### Documentation (this feature)

```text
specs/008-kv-cache-compression/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── kv-cache-interface.md
├── spec.md              # Feature specification (/speckit.specify command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
scripts/
├── quantization/
│   ├── kv_cache_compression.py      # NEW: KV cache compression manager
│   ├── kv_cache_profiles.py         # NEW: V2/V3 profile definitions
│   ├── config_builder.py            # MODIFY: extend for KV cache config
│   ├── quantization_manager.py      # MODIFY: integrate KV compression
│   └── ... (existing files)
├── server-lifecycle.py              # MODIFY: pass compression flags to mlx_lm.server
└── ... (existing files)

justfile                              # MODIFY: add compression mode recipes
```

**Structure Decision**: Extend existing `scripts/quantization/` directory with new KV cache compression modules. Follow the pattern established in spec 007 (hybrid quantization) for consistency. Modify `justfile` to expose compression controls.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

N/A - All gates pass.

## Phase 0: Research

*To be generated: `research.md`*

**Unknowns to Research**:
1. TurboQuant V2/V3 implementation details and integration patterns with MLX
2. Metal kernel compilation and runtime loading for custom quantization operations
3. Hybrid attention cache compatibility (KVCache, RotatingKVCache, ArraysCache) with compressed KV
4. Double-compression interaction between weight quantization (spec 007) and KV cache compression
5. Performance benchmarking methodology for compression ratio, speed, and quality metrics

**Research Tasks**:
- Research TurboQuant V2/V3 KV cache compression techniques for MLX
- Find best practices for Metal kernel integration in MLX inference pipelines
- Research hybrid attention cache handling with quantized KV caches
- Find patterns for runtime compression mode switching without server restart
- Research automatic compression strategy selection based on model size detection

## Phase 1: Design & Contracts

*To be generated: `data-model.md`, `contracts/kv-cache-interface.md`, `quickstart.md`*

**Design Tasks**:
1. Define `CompressionProfile` entity with V2/V3 paths and configuration
2. Design `KVCacheCompressionManager` service interface
3. Specify integration points with existing `QuantizationManager` (spec 007)
4. Define `just` recipe contracts for compression mode selection
5. Document fallback and error handling behaviors

## Phase 2: Implementation Planning

*To be generated by `/speckit.tasks` command: `tasks.md`*

**Implementation Order**:
1. Research completion (Phase 0)
2. Data model and contract definition (Phase 1)
3. Core KV cache compression modules
4. Integration with quantization manager
5. just recipe updates
6. Testing and validation
7. Documentation updates

---
*Generated by `/speckit.plan` command following `.specify/templates/plan-template.md`*
