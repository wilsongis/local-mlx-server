# Implementation Plan: Per-Path Hybrid Quantization

**Branch**: `007-hybrid-quantization` | **Date**: 2026-05-20 | **Spec**: [spec.md](specs/007-hybrid-quantization/spec.md)
**Input**: Feature specification from `specs/007-hybrid-quantization/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Implement per-path hybrid quantization configuration for MLX models on Apple Silicon, enabling different bit-widths for attention versus expert layers (e.g., tq3a-tq2e g32). Support latent-MoE architectures like Nemotron-3-Super-120B-A12B and provide Lloyd-Max codebook calibration option (Phase 2) referencing sharpner/turboquant-mlx V3 implementation.

## Technical Context

**Language/Version**: Python 3.11+ (MLX ecosystem compatibility)
**Primary Dependencies**: mlx-lm, mlx (Apple Silicon ML framework), PyYAML (profile parsing), numpy (calibration data)
**Storage**: YAML profiles in `scripts/wrapper-config/profiles.yaml`, binary MLX codebooks on filesystem
**Testing**: pytest (existing test infrastructure in `tests/`)
**Target Platform**: macOS on Apple Silicon (M-series chips with unified memory)
**Project Type**: Infrastructure/cli - local inference server configuration and quantization management
**Performance Goals**: 120B+ models loadable on 48GB systems, 20+ tok/s generation rate, <150% startup time vs uniform quantization
**Constraints**: Memory-constrained (48GB unified), must preserve OpenAI-compatible API via mlx_lm.server, reversible configuration changes
**Scale/Scope**: 4 new just recipes, 2-3 Python modules extended, YAML profile schema, health endpoint extension

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Status | Notes |
|------------------------|--------|-------|
| I. Infrastructure-Only Scope | ✅ PASS | Feature adds quantization config to server infrastructure only; no product/web UI code |
| II. Local Serving Reliability | ✅ PASS | Preserves mlx_lm.server OpenAI-compatible API; extends health endpoint with quantization status |
| III. Quantization and Memory First | ✅ PASS | Core feature directly addresses 120B+ model memory optimization via per-path hybrid quantization |
| IV. Just Command Bridge | ✅ PASS | New just recipes: quant-apply, quant-validate, quant-list, quant-calibrate, quant-status |
| V. Reversible, Testable Changes | ✅ PASS | YAML profiles are reversible; validation before apply; rollback on failure (NFR-005) |

**Gate Status**: ✅ ALL PASSED - No violations detected. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/007-hybrid-quantization/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── quantization-interface.md
├── spec.md              # Feature specification (input)
├── checklists/          # Quality gates
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
scripts/
├── wrapper-config/
│   ├── profiles.yaml    # Quantization profiles (tq3a-tq2e-g32, etc.)
│   └── presets.yaml     # Server presets
├── server-lifecycle.py  # Extended with quantization status
├── model-management.py  # Extended with quant-profile parameter
└── mlx_wrapper.py       # May integrate quantization config

tests/
├── test_server_lifecycle.py
├── test_main.py
└── test_health_accuracy.py

justfile                  # New recipes: quant-apply, quant-validate, quant-list, quant-calibrate, quant-status
```

**Structure Decision**: Single infrastructure project. Feature extends existing Python scripts (`scripts/`) and `justfile` with quantization-specific functionality. No new top-level directories needed. All quantization profiles stored in existing `scripts/wrapper-config/profiles.yaml`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
