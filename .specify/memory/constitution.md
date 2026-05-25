<!--
## Sync Impact Report

**Version change**: 2.0.0 → 2.1.0 (updated to match GOVERNANCE.md)

**Modified principles**: None

**Added sections**: None

**Removed sections**: None

**Templates requiring updates**:
- ✅ `.specify/templates/plan-template.md` - Constitution Check section present (line 30-34)
- ✅ `.specify/templates/spec-template.md` - No constitution-specific sections found (generic template)
- ✅ `.specify/templates/tasks-template.md` - No principle-driven task types required (generic template)
- ✅ Command files - No `.specify/templates/commands/` directory exists

**Follow-up TODOs**: None

**Verification date**: 2026-05-24

**Notes**: Constitution updated to version 2.1.0 to match GOVERNANCE.md. All principles remain aligned to AGENTS.md and README. No placeholders remain. Version 2.1.0 ratified 2026-03-06, last amended 2026-05-24. Admin GUI MVP (ADMIN-001) completed and reflected in project artifacts.
-->

# Local MLX Server Constitution

## Core Principles

### I. Infrastructure-Only Scope

This repository exists only for local inference infrastructure. Product web-stack features, application UI code, and general business app logic are out of scope.

### II. Local Serving Reliability

All changes must preserve or improve OpenAI-compatible local serving behavior through `mlx_lm.server`, with an emphasis on startup reliability, endpoint stability, and predictable runtime behavior.

### III. Quantization and Memory First

Optimization work must prioritize Apple Silicon memory constraints for 120B+ class models. Changes should focus on weight compression, per-path hybrid quantization, and KV cache compression behavior.

### IV. Just Command Bridge

Operational workflows must be expressed through `just` recipes. Routine start, stop, status, lint, and test operations should avoid ad-hoc shell command sequences.

### V. Reversible, Testable Changes

Edits should be minimal, reversible, and validated. Prefer incremental updates over broad refactors and keep operational scripts auditable.

## Additional Constraints

- `AGENTS.md` is the authoritative operational charter.
- Spec-driven workflows use `/speckit.*` commands.
- Runtime and operational workflows use `just` as the stable interface.

## Governance

This constitution and `AGENTS.md` govern project behavior. Any policy change that affects repository scope, runtime interface, or serving guarantees must update these documents together.

**Version**: 2.1.0 | **Ratified**: 2026-03-06 | **Last Amended**: 2026-05-24
