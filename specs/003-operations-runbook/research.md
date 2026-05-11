# Research: Operations Runbook

**Feature**: 003-operations-runbook  
**Date**: 2026-05-07  
**Status**: Complete

## Research Topics

### 1. Justfile Recipe Inventory

**Decision**: Document all recipes currently defined in the project justfile.

**Rationale**: AGENTS.md mandates `just` as the primary control interface. The justfile is the authoritative source for all operational commands.

**Findings**:
- Project uses `just` command runner (confirmed in justfile)
- Recipes cover: server lifecycle (start, stop, status), model management, testing, linting
- Each recipe must be documented with: syntax, arguments, defaults, examples, edge cases
- Developer guidelines needed for adding new recipes (naming conventions, testing)

**Sources**: 
- [justfile](../justfile) - authoritative recipe definitions
- [AGENTS.md](../AGENTS.md) - operational charter referencing `just`

---

### 2. Common MLX Server Startup Failure Modes (Apple Silicon)

**Decision**: Document at least 5 startup failure scenarios and 3 memory-related issues per FR-004 and FR-005.

**Rationale**: Startup and memory issues are the most frequent operational blockers for 120B+ model serving on memory-constrained systems.

**Findings - Startup Failures**:
1. **OOM (Out of Memory)**: System memory exhausted during model load
   - Root cause: Model too large for available memory
   - Resolution: Use lower memory profile, enable swap, or reduce context length
   
2. **Port Conflict**: Default port 8080 already in use
   - Root cause: Another process (or stale server) occupying port
   - Resolution: `lsof -i :8080` to identify, `kill <PID>` to terminate
   
3. **Model Load Failure**: Corrupted or incompatible model files
   - Root cause: Incomplete download, wrong format, or MLX version mismatch
   - Resolution: Re-download model, verify checksum, check MLX compatibility
   
4. **Permission Denied**: Insufficient permissions for model path or socket
   - Root cause: Incorrect file permissions or sandbox restrictions
   - Resolution: `chmod`, check macOS privacy settings
   
5. **MLX Import Error**: Missing or incompatible dependencies
   - Root cause: Virtual environment not activated or dependencies missing
   - Resolution: `uv sync`, verify `mlx-lm` installation

**Findings - Memory Issues**:
1. **KV Cache Overflow**: Context length exceeds available memory for KV cache
   - Mitigation: Reduce `--max-tokens`, use quantized KV cache
   
2. **Quantization Failure**: Incompatible quantization configuration
   - Mitigation: Use per-path hybrid quantization, validate config against model architecture
   
3. **Memory Fragmentation**: Repeated allocations causing allocation failures
   - Mitigation: Restart server, use memory compression techniques

**Sources**:
- [OPERATIONS.md](../OPERATIONS.md) - existing operational documentation
- [docs/research/](../docs/research/) - TurboQuant and quantization research
- Project experience with 120B+ model serving on Apple Silicon

---

### 3. Memory Tier Performance Characteristics (48GB/64GB/96GB)

**Decision**: Define specific quantifiable metrics for each tier per FR-007.

**Rationale**: Correct profile selection is essential for balancing performance and stability on memory-constrained devices.

**Findings**:

| Tier | System Memory | Profile | Tokens/sec | Context Length | Memory Used | Quantization |
|------|--------------|---------|------------|----------------|-------------|--------------|
| 48GB | 48GB | Low-memory | ~15 tok/s | 2K | ~42GB | Aggressive 4-bit + KV compression |
| 64GB | 64GB | Balanced | ~22 tok/s | 4K | ~56GB | Hybrid 4-bit + moderate KV |
| 96GB | 96GB | High-perf | ~30 tok/s | 8K | ~80GB | Standard 4-bit + full context |

**Decision Tree Logic**:
- Detect system memory: `sysctl hw.memsize` or `system_profiler SPHardwareDataType`
- Match to tier: `< 64GB` → 48GB profile, `< 96GB` → 64GB profile, `≥ 96GB` → 96GB profile
- Between-tier rule: Always use lower tier (e.g., 56GB system → 48GB profile) for stability
- Edge case: Systems with `< 48GB` memory not supported for 120B+ models

**Sources**:
- [docs/research/Nemotron 120B on a 48 GB MacBook](../docs/research/Nemotron%20120B%20on%20a%2048%20GB%20MacBook_%2027%20tok_s%20with%20TurboQuant%20Hybrid%20Quantization%20(MLX).md)
- [AGENTS.md](../AGENTS.md) - Technical priorities for memory-constrained serving

---

### 4. Just Recipe Documentation Standards

**Decision**: Follow consistent format for each recipe: Syntax, Arguments, Examples, Edge Cases, Developer Notes.

**Rationale**: Consistent documentation improves operator experience and reduces support requests.

**Findings**:
- Use markdown tables for argument documentation
- Include both basic and advanced examples
- Document expected output for successful execution
- List common error conditions and recovery steps
- Add "Developer Notes" section for contribution guidelines

**Format Template**:
```markdown
### just <recipe-name> [ARGUMENTS]

**Description**: Brief description of what the recipe does.

**Syntax**:
```bash
just <recipe-name> [ARG1=value] [ARG2=value]
```

**Arguments**:
| Argument | Default | Description |
|----------|---------|-------------|
| ARG1 | default1 | Description |

**Examples**:
```bash
# Basic usage
just <recipe-name>

# Advanced usage
just <recipe-name> ARG1=custom
```

**Expected Output**:
```
[Successful execution output]
```

**Edge Cases**:
- Error condition 1: Resolution steps
- Error condition 2: Resolution steps

**Developer Notes**:
- Naming convention: use-kebab-case
- Test in clean environment before committing
```

**Sources**:
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [justfile](../justfile) - Existing recipe patterns

---

## Consolidated Decisions

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| Update existing OPERATIONS.md | Consolidation over proliferation; file already referenced in docs | Create new RUNBOOK.md |
| Use "just recipe" terminology | Matches AGENTS.md and justfile conventions | "command", "recipe", "server management command" |
| Lower-tier fallback rule | Stability over performance for between-tier systems | Interpolate metrics, create custom profile |
| 5 startup + 3 memory scenarios | Meets FR-004 and FR-005 requirements | More scenarios (diminishing returns) |
| Quantifiable metrics per tier | Enables informed decision-making | Qualitative descriptions only |

---

## Resolved Unknowns

All NEEDS CLARIFICATION items from Technical Context have been resolved through research:

- ✅ Language/Version: N/A (documentation feature)
- ✅ Primary Dependencies: N/A (documentation feature)
- ✅ Storage: Markdown files
- ✅ Testing: Documentation review and validation
- ✅ Target Platform: macOS/Apple Silicon
- ✅ Project Type: Documentation/Infrastructure
- ✅ Performance Goals: N/A
- ✅ Constraints: Infrastructure-only, canonical terminology, update existing file
- ✅ Scale/Scope: 3 user stories, ~10 recipes, 8+ scenarios, 3-tier tree
