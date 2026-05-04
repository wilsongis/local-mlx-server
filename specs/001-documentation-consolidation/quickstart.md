# Quickstart: Documentation Consolidation

## Prerequisites

- Access to existing files: `README.md`, `AGENTS.md`, `.specify/memory/constitution.md`
- Understanding of markdown formatting
- Familiarity with Local MLX Server project structure

## Quick Start Steps

### 1. Understand the Current State

Read the three source files to understand existing content:

```bash
# Read current documentation
cat README.md
cat AGENTS.md
cat .specify/memory/constitution.md
```

### 2. Review the Plan

```bash
# Read the implementation plan
cat specs/001-documentation-consolidation/plan.md
```

Key points:
- 5-file structure: README.md (index), OPERATIONS.md, AGENTS.md, GOVERNANCE.md, CONTRIBUTING.md
- Persona-driven: Operators, Contributors, Maintainers
- 100% content preservation required

### 3. Content Mapping

Use the data model to understand content mapping:

| From | To | Content |
|------|----|---------|
| README.md | README.md, OPERATIONS.md | Overview → README; Operations → OPERATIONS.md |
| AGENTS.md | AGENTS.md, GOVERNANCE.md | Agent rules → AGENTS.md; Governance → GOVERNANCE.md |
| constitution.md | GOVERNANCE.md | All governance content → GOVERNANCE.md |

### 4. Create the Documentation Files

#### Step 4.1: Update README.md (Index)

Create README.md as the central navigation point:

```markdown
# Local MLX Server

## Quick Navigation by Persona

### 🖥️ Operators (Run the Server)
- [Operations Guide](OPERATIONS.md) - Server startup, just recipes, monitoring

### 👩‍💻 Contributors (Add Code/Docs)
- [Contributing Guide](CONTRIBUTING.md) - Setup, development workflow, testing
- [Agent Rules](AGENTS.md) - Operational charter, /speckit.* commands

### 🛡️ Maintainers (Governance)
- [Governance](GOVERNANCE.md) - Constitution, documentation standards, releases

## Project Overview
[Content from original README.md]
```

#### Step 4.2: Create OPERATIONS.md

```bash
# Extract operations content from README.md and create OPERATIONS.md
# Include: just recipes, server startup, troubleshooting
```

#### Step 4.3: Update AGENTS.md

```bash
# Preserve AGENTS.md content, ensure it links to GOVERNANCE.md for governance
```

#### Step 4.4: Create GOVERNANCE.md

```bash
# Combine constitution.md content with documentation standards
# Add: overview, setup, operations, agent rules, governance, contributions sections
```

#### Step 4.5: Create CONTRIBUTING.md

```bash
# Create contribution guidelines
# Include: setup, development workflow, testing, PR process
```

### 5. Verify Content Preservation

```bash
# Audit: Compare original files with new structure
# Ensure 100% of critical content is preserved

# Check original README.md content appears in README.md and/or OPERATIONS.md
# Check original AGENTS.md content appears in AGENTS.md and/or GOVERNANCE.md
# Check constitution.md content appears in GOVERNANCE.md
```

### 6. Validate Documentation Standards

```bash
# Check GOVERNANCE.md has at least 6 sections:
# 1. Overview/Purpose
# 2. Installation/Setup
# 3. Operations (just recipes)
# 4. Agent Rules (AGENTS.md content)
# 5. Governance (constitution)
# 6. Contributions

# Verify inference-specific content:
# - Model serving endpoints
# - Quantization/memory considerations
# - Apple Silicon constraints
# - mlx_lm.server compatibility
```

### 7. Test Navigation

```bash
# Persona navigation test:
# 1. Operator: Can you find server startup in < 2 minutes?
#    Path: README.md → OPERATIONS.md
#
# 2. Contributor: Can you find agent rules in < 2 minutes?
#    Path: README.md → AGENTS.md
#
# 3. Maintainer: Can you find governance in < 2 minutes?
#    Path: README.md → GOVERNANCE.md
```

## Success Criteria Checklist

- [ ] All 5 files created (README.md, OPERATIONS.md, AGENTS.md, GOVERNANCE.md, CONTRIBUTING.md)
- [ ] README.md links to all 4 other files
- [ ] Persona-specific navigation in README.md
- [ ] 100% critical content preserved (content audit passed)
- [ ] GOVERNANCE.md has 6+ sections with documentation standards
- [ ] Inference-specific standards in GOVERNANCE.md
- [ ] Cross-references in all files (min 2 per file)
- [ ] Consistent markdown formatting across all files

## Next Steps

After completing the documentation consolidation:

1. Run content audit to verify no content loss
2. Test navigation with each persona
3. Update any broken links
4. Commit changes using `just` or `/speckit.git.commit`
5. Proceed to implementation phase (`/speckit.implement`)

## Common Pitfalls

- **Content Loss**: Always audit original vs new content
- **Broken Links**: Test all internal links after consolidation
- **Missing Persona Paths**: Ensure README clearly shows paths for each persona
- **Inconsistent Formatting**: Use markdown linter on all files
- **Missing Inference-Specific Content**: Ensure GOVERNANCE.md addresses model serving, quantization, Apple Silicon
