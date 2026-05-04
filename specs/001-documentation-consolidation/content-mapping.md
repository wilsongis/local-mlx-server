# Content Mapping: Documentation Consolidation

## Source Files Analysis

### README.md (Original)
**Total Lines**: ~115 (shown in read)
**Sections Identified**:
1. Purpose (lines 3-8)
2. The Core Problem (lines 10-16)
3. Technical Solution: TurboQuant Methodology (lines 18-50)
4. What This Repository Is Building Toward (lines 52-60)
5. Operational Recommendation: Use Just As The Control Plane (lines 62-76)
6. Scope and Non-Goals (lines 91-104)
7. Operational Direction (lines 106-114)

**Content Mapping**:
| Content Section | Target File | Reason |
|-----------------|-------------|--------|
| Purpose | README.md (index) | Core project identity - belongs in index |
| The Core Problem | README.md (index) | Context for why project exists |
| Technical Solution | README.md (index) | Key technical differentiator |
| What This Repository Is Building Toward | README.md (index) | Project vision and goals |
| Operational Recommendation: Just | OPERATIONS.md | Operational workflow guidance |
| Scope and Non-Goals | README.md (index) | Project boundaries - index material |
| Operational Direction | OPERATIONS.md | Near-term operational priorities |

### AGENTS.md (Original)
**Total Lines**: 86
**Sections Identified**:
1. Agent Purpose (lines 3-12)
2. Command Standard (lines 14-36)
3. Repository Boundary (lines 38-51)
4. Technical Focus Rules (lines 53-64)
5. Change Discipline (lines 66-76)
6. Definition of Done for Agent Tasks (lines 78-85)

**Content Mapping**:
| Content Section | Target File | Reason |
|-----------------|-------------|--------|
| Agent Purpose | AGENTS.md | Core agent operational charter |
| Command Standard | AGENTS.md | Agent command namespace rules |
| Repository Boundary | GOVERNANCE.md | Governance/boundary rules |
| Technical Focus Rules | AGENTS.md | Agent technical priorities |
| Change Discipline | AGENTS.md | Agent workflow rules |
| Definition of Done | GOVERNANCE.md | Governance completion criteria |

### .specify/memory/constitution.md (Original)
**Total Lines**: 60
**Sections Identified**:
1. Core Principles (lines 27-47)
   - I. Infrastructure-Only Scope
   - II. Local Serving Reliability
   - III. Quantization and Memory First
   - IV. Just Command Bridge
   - V. Reversible, Testable Changes
2. Additional Constraints (lines 49-53)
3. Governance (lines 55-59)

**Content Mapping**:
| Content Section | Target File | Reason |
|-----------------|-------------|--------|
| Core Principles (all 5) | GOVERNANCE.md | Primary governance document |
| Additional Constraints | GOVERNANCE.md | Governance rules |
| Governance section | GOVERNANCE.md | Governance processes |

## Critical Content Preservation Checklist (Success Criterion SC-001)

### From README.md (7 sections)
- [ ] Purpose
- [ ] The Core Problem
- [ ] Technical Solution: TurboQuant Methodology
- [ ] What This Repository Is Building Toward
- [ ] Operational Recommendation: Just (→ OPERATIONS.md)
- [ ] Scope and Non-Goals
- [ ] Operational Direction (→ OPERATIONS.md)

### From AGENTS.md (6 sections)
- [ ] Agent Purpose
- [ ] Command Standard
- [ ] Repository Boundary (→ GOVERNANCE.md)
- [ ] Technical Focus Rules
- [ ] Change Discipline
- [ ] Definition of Done (→ GOVERNANCE.md)

### From constitution.md (3 sections)
- [ ] Core Principles (all 5 principles)
- [ ] Additional Constraints
- [ ] Governance section

## Target File Outlines

### README.md (Index)
```
# Local MLX Server
## Quick Navigation by Persona
### 🖥️ Operators
### 👩‍💻 Contributors
### 🛡️ Maintainers
## Project Overview (from original README)
## The Core Problem
## Technical Solution
## Scope and Non-Goals
## Links to Other Docs
```

### OPERATIONS.md
```
# Operations Guide
## Just Command Reference
## Server Startup
## Server Lifecycle Management
## Model Management
## Troubleshooting
## Operational Direction (from README)
```

### AGENTS.md (Updated)
```
# AGENTS.md: Local MLX Server Operations Charter
## 1. Agent Purpose
## 2. Command Standard (Mandatory)
## 3. Technical Focus Rules
## 4. Change Discipline
## 5. Definition of Done for Agent Tasks
## Cross-References
```

### GOVERNANCE.md
```
# Governance
## Core Principles (from constitution)
### I. Infrastructure-Only Scope
### II. Local Serving Reliability
### III. Quantization and Memory First
### IV. Just Command Bridge
### V. Reversible, Testable Changes
## Additional Constraints
## Repository Boundary (from AGENTS.md)
## Definition of Done (from AGENTS.md)
## Documentation Standards
### Overview/Purpose Standards
### Installation/Setup Standards
### Operations Standards
### Agent Rules Standards
### Governance Standards
### Contribution Standards
## Inference-Specific Standards
### Model Serving Endpoints
### Quantization/Memory Considerations
### Apple Silicon Constraints
### mlx_lm.server Compatibility
```

### CONTRIBUTING.md
```
# Contributing to Local MLX Server
## Getting Started
## Development Workflow
## Testing Guidelines
## Code Style
## Pull Request Process
## Documentation Standards Reference
```
