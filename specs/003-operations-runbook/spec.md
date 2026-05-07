# Feature Specification: Operations Runbook

**Feature Branch**: `003-operations-runbook`
**Created**: 2026-05-06
**Status**: Draft
**Input**: User description: "DOC-003: Create operations runbook spec via /speckit.specify. Document all just recipes with examples and edge cases. Create troubleshooting guide for common startup/memory issues. Define model profile selection decision tree (48GB vs 64GB vs 96GB tiers). Target: /speckit.plan → /speckit.tasks → /speckit.implement"

## Clarifications

### Session 2026-05-06

- Q: What approach should be used to define quantifiable metrics for each profile (tokens/second, context length, memory overhead) for the 48GB/64GB/96GB tiers? → A: Define specific targets per profile (e.g., 48GB: 15 tok/s, 2K context, 42GB used)
- Q: How should the runbook address different user roles (operators vs developers)? → A: Differentiate by role: operators need runbook + troubleshooting; developers need justfile contribution guidelines
- Q: How should the model profile decision tree handle systems with memory between the defined tiers (e.g., 56GB between 48GB and 64GB tiers)? → A: Use lower tier (56GB system uses 48GB profile) to ensure stability
- Q: What should be the canonical terminology for the runbook (currently uses "just recipes", "recipes", "commands", "server management commands" interchangeably)? → A: Standardize on 'just recipe' (matches justfile terminology and AGENTS.md)
- Q: The spec requires creating runbook documentation but doesn't specify the deliverable format. Should the runbook update the existing OPERATIONS.md or create a new file (e.g., RUNBOOK.md)? → A: Update existing OPERATIONS.md to consolidate operational docs

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Document all just recipes with examples and edge cases (Priority: P1)

**Operators** need clear documentation of all available `just` recipes to reliably manage the local MLX server lifecycle without referring to source code. **Developers** need contribution guidelines for adding/modifying `just` recipes following project patterns.

**Why this priority**: Core operational workflows depend on `just` as the primary control interface per AGENTS.md. Without documentation, users cannot discover or correctly use `just` recipes.

**Independent Test**: Can be fully tested by reviewing the runbook to confirm every `just` recipe in the justfile is documented with usage examples and edge case handling.

**Acceptance Scenarios**:

1. **Given** an operator has the runbook (OPERATIONS.md), **When** they look up a `just` recipe, **Then** they see the command syntax, required arguments, and example usage.
2. **Given** a developer wants to add a new `just` recipe, **When** they consult the runbook (OPERATIONS.md), **Then** they find contribution guidelines and code patterns to follow.
3. **Given** a user runs a `just` recipe with invalid arguments, **When** they consult the runbook (OPERATIONS.md), **Then** they find documented edge cases and error handling guidance.

---

### User Story 2 - Create troubleshooting guide for common startup/memory issues (Priority: P1)

Operators need a structured troubleshooting guide to quickly resolve common server startup failures and memory-related issues on Apple Silicon memory-constrained systems.

**Why this priority**: Startup and memory issues are the most frequent operational blockers for 120B+ model serving on Apple Silicon. Fast resolution is critical for server reliability.

**Independent Test**: Can be fully tested by simulating common failure scenarios (OOM, port conflicts, model load failures) and verifying the guide provides correct resolution steps.

**Acceptance Scenarios**:

1. **Given** the server fails to start due to insufficient memory, **When** the operator consults the troubleshooting guide in OPERATIONS.md, **Then** they find step-by-step instructions to adjust quantization or model profile.
2. **Given** the server port is already in use, **When** the operator checks the guide in OPERATIONS.md, **Then** they find commands to identify and terminate conflicting processes.
3. **Given** a model fails to load, **When** the operator follows the guide in OPERATIONS.md, **Then** they can diagnose whether the issue is model path, corruption, or compatibility.

---

### User Story 3 - Define model profile selection decision tree (48GB vs 64GB vs 96GB tiers) (Priority: P1)

Operators need a clear decision tree to select the correct model profile based on available system memory to optimize for 120B+ model serving viability.

**Why this priority**: Correct profile selection is essential for balancing model performance and system stability on memory-constrained Apple Silicon devices.

**Independent Test**: Can be fully tested by verifying the decision tree correctly maps system memory tiers to recommended profiles with quantifiable rationale.

**Acceptance Scenarios**:

1. **Given** an operator has a 48GB memory system, **When** they follow the decision tree in OPERATIONS.md, **Then** they are directed to the appropriate low-memory profile with expected token/s performance.
2. **Given** an operator has a 96GB memory system, **When** they consult the decision tree in OPERATIONS.md, **Then** they select a high-performance profile with maximum context length.
3. **Given** an operator has a 56GB memory system (between tiers), **When** they follow the decision tree in OPERATIONS.md, **Then** they are directed to the 48GB profile to ensure system stability.
4. **Given** an operator is unsure of their system memory, **When** they use the decision tree in OPERATIONS.md, **Then** they find commands to check their available memory and model requirements.

---

### Edge Cases

- What happens when a `just` recipe is deprecated or renamed?
- How does the troubleshooting guide handle multiple simultaneous issues (e.g., OOM + port conflict)?
- How to handle model profiles not covered by the 48/64/96GB tiers?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: OPERATIONS.md MUST document all `just` recipes currently defined in the project justfile with command syntax, required arguments, and default values.
- **FR-002**: OPERATIONS.md MUST provide at least one working example for each `just` recipe with expected output.
- **FR-003**: OPERATIONS.md MUST document edge cases for each `just` recipe including error conditions, invalid inputs, and recovery steps.
- **FR-004**: OPERATIONS.md troubleshooting guide MUST cover at least 5 common startup failure scenarios with root cause analysis and resolution steps.
- **FR-005**: OPERATIONS.md troubleshooting guide MUST cover at least 3 memory-related issues (OOM, KV cache overflow, quantization failures) with mitigation strategies.
- **FR-006**: OPERATIONS.md decision tree MUST clearly map 48GB, 64GB, and 96GB memory tiers to recommended model profiles.
- **FR-007**: Decision tree MUST include specific quantifiable metrics for each profile:
  - 48GB tier: ~15 tok/s, 2K context length, ~42GB memory used
  - 64GB tier: ~22 tok/s, 4K context length, ~56GB memory used
  - 96GB tier: ~30 tok/s, 8K context length, ~80GB memory used
- **FR-008**: OPERATIONS.md MUST follow the operational scope defined in AGENTS.md (infrastructure-only, no full-stack components).
- **FR-009**: All documentation MUST use the `just` command interface as the primary control mechanism per project standards. Canonical terminology: "just recipe" (not "command", "recipe", or "server management command").
- **FR-010**: OPERATIONS.md MUST include a "Developer Guidelines" section covering justfile contribution standards, recipe naming conventions, and testing requirements for new recipes.
- **FR-011**: Decision tree MUST use lower-tier fallback rule: systems with memory between defined tiers (e.g., 56GB) MUST use the lower tier profile (48GB profile) to ensure stability over performance.

### Key Entities *(include if feature involves data)*

- **Just Recipe**: Command name, syntax, arguments, examples, edge cases, related troubleshooting, developer notes
- **Troubleshooting Scenario**: Issue type, symptoms, root cause, resolution steps, prevention tips
- **Model Profile**: Memory tier, profile name, quantization config, performance metrics, compatibility, fallback rules

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of `just` recipes in the justfile are documented in OPERATIONS.md with examples within 1 week of feature completion.
- **SC-002**: Operators can resolve 80% of common startup/memory issues using only the troubleshooting guide in OPERATIONS.md without additional support.
- **SC-003**: Model profile selection accuracy improves to 95% (correct profile chosen for given memory tier) using the decision tree in OPERATIONS.md.
- **SC-004**: New operators can complete server startup and model selection tasks in under 5 minutes using OPERATIONS.md.
- **SC-005**: Updated OPERATIONS.md reduces operational support requests related to `just` recipe usage and profile selection by 50% within 1 month of release.
- **SC-006**: Developers can add new `just` recipes following documented contribution guidelines in OPERATIONS.md without additional mentorship.
- **SC-007**: Decision tree correctly handles 100% of edge cases including between-tier memory systems (e.g., 56GB, 80GB).
- **SC-008**: Documentation uses consistent terminology ("just recipe") throughout with 100% compliance in final review.

## Assumptions

- The project's justfile is the authoritative source for all `just` recipes.
- Troubleshooting scenarios are specific to Apple Silicon (M-series) systems running local MLX inference servers.
- Model profiles are pre-defined in the project's configuration and align with 48GB, 64GB, and 96GB memory tiers.
- Operators have basic familiarity with command-line interfaces and system monitoring tools.
- Developers contributing to justfile have basic knowledge of `just` command syntax and shell scripting.
- Systems with memory between defined tiers will prioritize stability by using the lower tier profile.
- Canonical terminology "just recipe" will be used consistently throughout all runbook documentation.
- The existing OPERATIONS.md file will be updated (not replaced) to consolidate all operational documentation.
