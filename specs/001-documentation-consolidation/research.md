# Research: Documentation Consolidation

## Overview

Research findings to support the documentation consolidation feature for the Local MLX Server project.

## Decision Log

### Decision: Multi-file Documentation Structure

**Decision**: Use a multi-file structure with README.md as index, plus OPERATIONS.md, AGENTS.md, GOVERNANCE.md, and CONTRIBUTING.md

**Rationale**:
- Single consolidated file would be too long and harder to navigate
- Multi-file structure allows persona-based organization (Operators → OPERATIONS.md, Contributors → CONTRIBUTING.md, Maintainers → GOVERNANCE.md)
- README.md as index provides central navigation point
- Aligns with user clarifications specifying this exact structure

**Alternatives considered**:
- Single consolidated DOCUMENTATION.md file - Rejected: Too long, harder to find persona-specific content
- Docs folder with all files - Rejected: Root-level files more visible for infrastructure project
- Separate docs/ folder with index - Rejected: Adds navigation complexity; root-level preferred for small infrastructure projects

### Decision: Documentation Standards in GOVERNANCE.md

**Decision**: Define documentation standards specific to inference infrastructure projects in GOVERNANCE.md

**Rationale**:
- Maintainers need clear governance rules for documentation
- Inference infrastructure has unique concerns (model serving, quantization, Apple Silicon constraints)
- Standards should be reusable for other inference infrastructure projects
- Aligns with Constitution Principle I (Infrastructure-Only Scope)

**Alternatives considered**:
- Generic documentation standards - Rejected: Doesn't address inference-specific needs
- Standards in README.md - Rejected: README should be navigation-focused, not governance-focused
- Separate STANDARDS.md file - Rejected: GOVERNANCE.md is the appropriate home for governance/standards

### Decision: Content Preservation Strategy

**Decision**: Audit-based approach to ensure 100% critical content preservation from README.md, AGENTS.md, and constitution

**Rationale**:
- Success criterion SC-001 requires 100% critical content preservation
- Manual audit provides highest confidence
- Cross-reference mapping ensures no content is lost during consolidation

**Alternatives considered**:
- Automated diff tools - Rejected: Markdown restructuring makes automated comparison difficult
- Selective extraction - Rejected: Risk of missing critical content
- Full content copy - Rejected: Defeats purpose of consolidation; needs reorganization

## Best Practices Research

### Documentation Structure for Infrastructure Projects

**Findings**:
- README.md should be a landing page with clear navigation paths
- Operations/runbooks should be separate from governance/contribution docs
- Persona-based organization improves findability
- Cross-references between related docs essential for navigation

**Sources**:
- Open source infrastructure project conventions (Terraform, Kubernetes, Prometheus)
- Documentation systems research for technical projects

### Markdown Documentation Standards

**Findings**:
- Consistent heading levels (H1 for file title, H2 for major sections, H3 for sub-sections)
- Code blocks with language specifiers (```bash, ```python, etc.)
- Tables for structured data (comparison, navigation)
- Badges/icons sparingly for visual hierarchy
- Internal links using relative paths

**Application**:
- All 5 documentation files will follow consistent markdown formatting
- Code blocks will specify language (bash for just recipes, python for MLX examples)
- Tables for navigation in README.md index

### Inference Infrastructure Documentation Requirements

**Findings**:
- Must document: model endpoints, quantization configs, memory constraints
- Operational commands (just recipes) need prominent placement
- Hardware-specific notes (Apple Silicon) should be highlighted
- OpenAI-compatible API behavior must be documented for users migrating from cloud APIs

**Application**:
- OPERATIONS.md will prominently feature just recipes and server startup
- GOVERNANCE.md standards will mandate documentation of inference-specific concerns
- AGENTS.md content preserved as authoritative operational charter

## Open Questions Resolved

| Question | Resolution |
|----------|-------------|
| Should documentation be single or multi-file? | Multi-file with README index (from clarifications) |
| How to handle persona navigation? | README index with persona-specific paths |
| Where to put documentation standards? | GOVERNANCE.md (governance home) |
| How to verify content preservation? | Content audit against original files |

## Conclusion

Research confirms the multi-file documentation structure with persona-based organization is the optimal approach. Documentation standards in GOVERNANCE.md should address inference infrastructure specifics. Content preservation audit is required to meet success criteria.
