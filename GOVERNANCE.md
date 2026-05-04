# Governance

This document defines the governance structure, core principles, and documentation standards for the Local MLX Server project.

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

## Repository Boundary

This repository is an isolated infrastructure hub, not a full-stack application workspace.

Agents must keep it as a pure, lightweight inference server and must not introduce standard app-stack components in this directory.

Explicitly prohibited here:

- FastAPI application feature development
- HTMX page or UI integration
- PostGIS schema or spatial app logic
- General product web stack expansion

If a request requires app-level work, route it to the appropriate application repository.

## Definition of Done for Agent Tasks

A task is complete only when:

- It stays within infrastructure-only scope.
- It uses /speckit.* command structure where commands are involved.
- It does not introduce forbidden full-stack components.
- It preserves or improves local inference operability for the intended large-model workload.

## Documentation Standards

These standards define how inference infrastructure projects should document their architecture, operations, and agent rules. They are reusable for other inference infrastructure projects.

### 1. Overview/Purpose Standards

Every documentation set must include:

- Clear project purpose statement
- Target hardware/platform (e.g., Apple Silicon)
- Problem being solved (e.g., memory pressure for 120B+ models)
- High-level technical approach (e.g., TurboQuant-MLX methodology)

### 2. Installation/Setup Standards

Documentation must cover:

- Dependency management approach (e.g., `uv` for Python)
- Environment setup steps
- Model acquisition and placement
- Verification steps (health checks)

### 3. Operations Standards

Operations documentation must include:

- `just` recipe reference table with descriptions
- Server startup procedures (native and containerized)
- Server lifecycle management (start, stop, status)
- Model management (list, switch profiles)
- Troubleshooting section with common issues and solutions
- Operational direction and priorities

### 4. Agent Rules Standards

Agent-specific documentation (AGENTS.md) must define:

- Agent purpose and scope
- Command standards (e.g., `/speckit.*` namespace)
- Technical focus priorities
- Change discipline guidelines
- Definition of done criteria

### 5. Governance Standards

Governance documentation must include:

- Core principles (5+ principles recommended)
- Repository boundaries and prohibitions
- Additional constraints
- Version history with ratification and amendment dates

### 6. Contribution Standards

Contribution documentation must cover:

- Getting started (fork, clone, setup)
- Development workflow (branches, commits, PRs)
- Testing guidelines
- Code style requirements
- Pull request process

## Inference-Specific Standards

For inference infrastructure projects, documentation must address:

### Model Serving Endpoints

- Document OpenAI-compatible API endpoints
- Specify supported endpoints (e.g., `/v1/chat/completions`)
- Document any deviations from OpenAI API spec
- Include example requests and responses

### Quantization/Memory Considerations

- Document quantization methodology (e.g., TurboQuant)
- Specify per-path hybrid quantization approach
- Document KV cache compression techniques
- Include memory requirement estimates for target model sizes

### Apple Silicon Constraints

- Document unified memory considerations
- Specify tested hardware tiers (e.g., 64 GB, 96 GB)
- Note Metal GPU acceleration requirements
- Document any platform-specific optimizations

### mlx_lm.server Compatibility

- Document mlx_lm.server version requirements
- Specify compatible MLX versions
- Note any custom patches or modifications
- Document startup flags and their effects

## Governance Process

This constitution and `AGENTS.md` govern project behavior. Any policy change that affects repository scope, runtime interface, or serving guarantees must update these documents together.

**Version**: 2.0.0 | **Ratified**: 2026-03-06 | **Last Amended**: 2026-05-04

## Related Documentation

- [README](README.md) - Project overview and navigation index
- [Operations Guide](OPERATIONS.md) - Server operations and `just` recipes
- [Agent Rules](AGENTS.md) - Operational charter for AI agents
- [Contributing](CONTRIBUTING.md) - Contribution guidelines and development workflow
