# Quickstart: Operations Runbook

**Feature**: 003-operations-runbook  
**Date**: 2026-05-07  
**Status**: Complete

## Overview

This quickstart guide helps operators and developers get up to speed with the local MLX server operations using the updated OPERATIONS.md runbook.

## For Operators

### Prerequisites

- Local MLX server repository cloned and dependencies installed (`uv sync`)
- macOS system with Apple Silicon (M-series) chip
- Basic familiarity with terminal and command-line interfaces

### Quick Start: Your First Server Start

1. **Check your system memory**:
   ```bash
   system_profiler SPHardwareDataType | grep "Memory:"
   # Example output: Memory: 64 GB
   ```

2. **Select the correct model profile** using the decision tree:
   - 48GB system → Use low-memory profile (~15 tok/s, 2K context)
   - 64GB system → Use balanced profile (~22 tok/s, 4K context)
   - 96GB system → Use high-performance profile (~30 tok/s, 8K context)
   - **Between tiers?** (e.g., 56GB) → Use lower tier (48GB profile) for stability

3. **Start the server** using `just`:
   ```bash
   # Basic start (uses defaults)
   just start-server
   
   # Or with specific profile
   just start-server PROFILE=balanced
   ```

4. **Verify it's running**:
   ```bash
   just status
   # Expected: Server is running on http://localhost:8080
   ```

### Common Tasks

| Task | Command | Reference |
|------|---------|-----------|
| Start server | `just start-server` | [Just Recipe Reference](../OPERATIONS.md#just-recipe-reference) |
| Stop server | `just stop-server` | [Just Recipe Reference](../OPERATIONS.md#just-recipe-reference) |
| Check status | `just status` | [Just Recipe Reference](../OPERATIONS.md#just-recipe-reference) |
| View logs | `just logs` | [Just Recipe Reference](../OPERATIONS.md#just-recipe-reference) |
| Diagnose issues | `just doctor` | [Troubleshooting Guide](../OPERATIONS.md#troubleshooting-guide) |

### When Things Go Wrong

1. **Server won't start** → Check [Startup Failures](../OPERATIONS.md#startup-failures) in Troubleshooting Guide
2. **Out of memory errors** → Check [Memory Issues](../OPERATIONS.md#memory-issues) and verify your profile selection
3. **Port already in use** → Follow [Port Conflict Resolution](../OPERATIONS.md#port-conflicts) steps
4. **Model won't load** → See [Model Load Failures](../OPERATIONS.md#model-load-failures) section

---

## For Developers

### Prerequisites

- Familiarity with `just` command syntax and shell scripting
- Understanding of the project's [AGENTS.md](../AGENTS.md) operational charter
- Python virtual environment set up with `uv sync`

### Quick Start: Adding a New Just Recipe

1. **Read the contribution guidelines** in [Developer Guidelines](../OPERATIONS.md#developer-guidelines)

2. **Follow naming conventions**:
   - Use kebab-case: `my-new-recipe` (not `my_new_recipe` or `myNewRecipe`)
   - Use descriptive verbs: `start-server`, `check-status`, `run-tests`

3. **Add recipe to justfile**:
   ```bash
   # Example recipe template
   my-new-recipe ARG1="default1" ARG2="default2":
       # Recipe description
       echo "Running my-new-recipe with ARG1={{ARG1}}"
       # ... implementation
   ```

4. **Document the recipe** in OPERATIONS.md following the standard format:
   - Syntax
   - Arguments (table)
   - Examples (at least one)
   - Expected output
   - Edge cases
   - Developer notes

5. **Test your recipe**:
   ```bash
   # Test basic usage
   just my-new-recipe
   
   # Test with custom arguments
   just my-new-recipe ARG1=custom
   
   # Verify it handles errors gracefully
   just my-new-recipe ARG1=invalid
   ```

### Recipe Contribution Checklist

- [ ] Recipe follows kebab-case naming convention
- [ ] Recipe has clear description comment
- [ ] Arguments have sensible defaults
- [ ] Recipe is documented in OPERATIONS.md (syntax, arguments, examples, edge cases)
- [ ] Recipe handles error conditions gracefully
- [ ] Recipe tested in clean environment
- [ ] No ad-hoc shell sequences (use `just` as the interface per AGENTS.md)

---

## Model Profile Decision Tree (Quick Reference)

```
START: Check system memory
   │
   ├─ < 64GB ──────────────→ 48GB Profile
   │                          • ~15 tok/s
   │                          • 2K context
   │                          • ~42GB used
   │
   ├─ < 96GB ──────────────→ 64GB Profile
   │                          • ~22 tok/s
   │                          • 4K context
   │                          • ~56GB used
   │
   └─ ≥ 96GB ──────────────→ 96GB Profile
                              • ~30 tok/s
                              • 8K context
                              • ~80GB used

BETWEEN TIERS? (e.g., 56GB, 80GB)
  → Always use LOWER tier for stability
```

**Command to check memory**:
```bash
system_profiler SPHardwareDataType | grep "Memory:"
# or
sysctl hw.memsize | awk '{print $2/1024/1024/1024 " GB"}'
```

---

## Next Steps

### For Operators
1. Read the full [Just Recipe Reference](../OPERATIONS.md#just-recipe-reference) section
2. Familiarize yourself with the [Troubleshooting Guide](../OPERATIONS.md#troubleshooting-guide)
3. Bookmark the [Model Profile Decision Tree](../OPERATIONS.md#model-profile-decision-tree)
4. Practice common workflows: start → status → stop → restart

### For Developers
1. Review [Developer Guidelines](../OPERATIONS.md#developer-guidelines) in detail
2. Study existing recipes in [`justfile`](../justfile) for patterns
3. Read [CONTRIBUTING.md](../CONTRIBUTING.md) for general contribution workflow
4. Join the discussion on recipe proposals before implementing major changes

---

## Getting Help

- **Documentation**: Start with [OPERATIONS.md](../OPERATIONS.md)
- **Issues**: Check existing GitHub issues or create a new one
- **Discussions**: Use GitHub Discussions for questions about `just` recipe usage or contribution
- **Emergency**: For critical production issues, escalate per your organization's incident response process

---

## Validation

After reading this quickstart, you should be able to:
- [ ] Check your system memory and select the correct model profile
- [ ] Start and stop the MLX server using `just` recipes
- [ ] Diagnose common startup failures using the troubleshooting guide
- [ ] (Developers) Add a new `just` recipe following contribution guidelines
- [ ] (Developers) Document a recipe in OPERATIONS.md with all required sections

## Documentation Standards

- Use "just recipe" as the canonical terminology (not "just command", "recipe", or "command")
- Reference OPERATIONS.md sections with correct anchors:
  - `#just-recipe-reference` → Just Recipe Reference section
  - `#troubleshooting-guide` → Troubleshooting Guide section
  - `#model-profile-decision-tree` → Model Profile Decision Tree section
  - `#developer-guidelines` → Developer Guidelines section
- Include file paths as clickable links: [`justfile`](../justfile)
