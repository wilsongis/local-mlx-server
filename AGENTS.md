# AGENTS.md: Local MLX Server Operations Charter

## 1. Agent Purpose

You are operating inside a dedicated local inference infrastructure repository.

Your job is to maintain and improve this server layer only:

- Maintain local server startup and health-check workflows.
- Optimize inference arguments for memory, latency, and output stability.
- Manage MLX and TurboQuant dependency updates with minimal disruption.
- Preserve OpenAI-compatible local API serving behavior via mlx_lm.server.

## 2. Command Standard (Mandatory)

All spec-driven development and system commands in this repository must use the hardened speckit command namespace.

Required prefix:

- /speckit.*

Examples:

- /speckit.specify
- /speckit.plan
- /speckit.tasks
- /speckit.implement
- /speckit.verify

Do not use alternate command namespaces for planning, tasking, implementation, or verification inside this repository.

For runtime operations (server lifecycle, status checks, and model profile selection), use the `just` command bridge as the primary control interface.

- Prefer `just <command>` over ad-hoc direct shell invocations.
- Keep operational workflows reproducible and scriptable through `justfile` recipes.
- Treat `just` as the stable API that future external tools or UIs can call.

## 3. Repository Boundary (Strict)

This repository is an isolated infrastructure hub, not a full-stack application workspace.

Agents must keep it as a pure, lightweight inference server and must not introduce standard app-stack components in this directory.

Explicitly prohibited here:

- FastAPI application feature development
- HTMX page or UI integration
- PostGIS schema or spatial app logic
- General product web stack expansion

If a request requires app-level work, route it to the appropriate application repository.

## 4. Technical Focus Rules

Prioritize changes that improve local 120B+ serving viability on Apple Silicon memory-constrained systems.

Primary technical priorities:

- Weight compression integration health
- Per-path hybrid quantization configuration support
- KV cache compression behavior and stability
- Server runtime flags and argument presets
- Compatibility with uv-managed environments
- OpenAI-compatible endpoint reliability through mlx_lm.server

## 5. Change Discipline

When making changes:

- Keep the server surface minimal.
- Prefer reversible, testable edits.
- Avoid architecture drift toward product code.
- Document operational rationale for inference-related parameter changes.
- Validate that startup and serving flows remain functional after dependency updates.
- When introducing new operational actions, add or update `just` recipes first instead of adding manual command instructions.
- If a web UI is requested, keep it in a separate repository or directory boundary and have it call this repo's `just` commands.

## 6. Definition of Done for Agent Tasks

A task is complete only when:

- It stays within infrastructure-only scope.
- It uses /speckit.* command structure where commands are involved.
- It does not introduce forbidden full-stack components.
- It preserves or improves local inference operability for the intended large-model workload.
