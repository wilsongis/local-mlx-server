# Agent Directives: Local MLX Server Protocol

As an AI assistant working in this repository, prioritize local inference infrastructure changes only.

## 1. Single Source of Truth
The file `AGENTS.md` in the repository root is the authoritative operating charter.
Do not maintain project state in this file.

## 2. Core Operational Rules
1. **READ**: Read `AGENTS.md` before starting work.
2. **EXECUTE**: Use `just <command>` as the primary operational interface.
3. **WRITE**: Keep `AGENTS.md` aligned with durable operational policy updates.

## 3. Scope Guardrails
- Keep changes focused on local MLX/TurboQuant serving workflows.
- Preserve OpenAI-compatible local serving via `mlx_lm.server`.
- Do not introduce product web stack development in this repository.

## 4. Grounding
Use `/docs/research/` for methodology and tuning rationale when needed.

## Behavioral Trigger
"Take a deep breath and work on this problem step by step."