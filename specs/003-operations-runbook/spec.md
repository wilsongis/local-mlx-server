# Feature Specification: Operations Runbook

**Feature Branch**: `003-operations-runbook`
**Created**: 2026-05-06
**Status**: Draft
**Input**: User description: "DOC-003: Create operations runbook spec via /speckit.specify. Document all just recipes with examples and edge cases. Create troubleshooting guide for common startup/memory issues. Define model profile selection decision tree (48GB vs 64GB vs 96GB tiers). Target: /speckit.plan → /speckit.tasks → /speckit.implement"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Document all just recipes with examples and edge cases (Priority: P1)

Operators and developers need clear documentation of all available `just` recipes to reliably manage the local MLX server lifecycle without referring to source code.

**Why this priority**: Core operational workflows depend on `just` as the primary control interface per AGENTS.md. Without documentation, users cannot discover or correctly use server management commands.

**Independent Test**: Can be fully tested by reviewing the runbook to confirm every `just` recipe in the justfile is documented with usage examples and edge case handling.

**Acceptance Scenarios**:

1. **Given** a user has the runbook, **When** they look up a `just` recipe, **Then** they see the command syntax, required arguments, and example usage.
2. **Given** a user runs a `just` recipe with invalid arguments, **When** they consult the runbook, **Then** they find documented edge cases and error handling guidance.
3. **Given** a new `just` recipe is added to the justfile, **When** the runbook is updated, **Then** the new recipe is documented following the established template.

---

### User Story 2 - Create troubleshooting guide for common startup/memory issues (Priority: P1)

Operators need a structured troubleshooting guide to quickly resolve common server startup failures and memory-related issues on Apple Silicon memory-constrained systems.

**Why this priority**: Startup and memory issues are the most frequent operational blockers for 120B+ model serving on Apple Silicon. Fast resolution is critical for server reliability.

**Independent Test**: Can be fully tested by simulating common failure scenarios (OOM, port conflicts, model load failures) and verifying the guide provides correct resolution steps.

**Acceptance Scenarios**:

1. **Given** the server fails to start due to insufficient memory, **When** the operator consults the troubleshooting guide, **Then** they find step-by-step instructions to adjust quantization or model profile.
2. **Given** the server port is already in use, **When** the operator checks the guide, **Then** they find commands to identify and terminate conflicting processes.
3. **Given** a model fails to load, **When** the operator follows the guide, **Then** they can diagnose whether the issue is model path, corruption, or compatibility.

---

### User Story 3 - Define model profile selection decision tree (48GB vs 64GB vs 96GB tiers) (Priority: P1)

Operators need a clear decision tree to select the correct model profile based on available system memory to optimize for 120B+ model serving viability.

**Why this priority**: Correct profile selection is essential for balancing model performance and system stability on memory-constrained Apple Silicon devices.

**Independent Test**: Can be fully tested by verifying the decision tree correctly maps system memory tiers to recommended profiles with quantifiable rationale.

**Acceptance Scenarios**:

1. **Given** an operator has a 48GB memory system, **When** they follow the decision tree, **Then** they are directed to the appropriate low-memory profile with expected token/s performance.
2. **Given** an operator has a 96GB memory system, **When** they consult the decision tree, **Then** they select a high-performance profile with maximum context length.
3. **Given** an operator is unsure of their system memory, **When** they use the decision tree, **Then** they find commands to check their available memory and model requirements.

---

### Edge Cases

- What happens when a `just` recipe is deprecated or renamed?
- How does the troubleshooting guide handle multiple simultaneous issues (e.g., OOM + port conflict)?
- What if system memory falls between tiers (e.g., 56GB)?
- How to handle model profiles not covered by the 48/64/96GB tiers?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Runbook MUST document all `just` recipes currently defined in the project justfile with command syntax, required arguments, and default values.
- **FR-002**: Runbook MUST provide at least one working example for each `just` recipe with expected output.
- **FR-003**: Runbook MUST document edge cases for each `just` recipe including error conditions, invalid inputs, and recovery steps.
- **FR-004**: Troubleshooting guide MUST cover at least 5 common startup failure scenarios with root cause analysis and resolution steps.
- **FR-005**: Troubleshooting guide MUST cover at least 3 memory-related issues (OOM, KV cache overflow, quantization failures) with mitigation strategies.
- **FR-006**: Model profile decision tree MUST clearly map 48GB, 64GB, and 96GB memory tiers to recommended model profiles.
- **FR-007**: Decision tree MUST include quantifiable metrics for each profile: expected tokens/second, maximum context length, and memory overhead.
- **FR-008**: Runbook MUST follow the operational scope defined in AGENTS.md (infrastructure-only, no full-stack components).
- **FR-009**: All documentation MUST use the `just` command interface as the primary control mechanism per project standards.

### Key Entities *(include if feature involves data)*

- **Just Recipe**: Command name, syntax, arguments, examples, edge cases, related troubleshooting
- **Troubleshooting Scenario**: Issue type, symptoms, root cause, resolution steps, prevention tips
- **Model Profile**: Memory tier, profile name, quantization config, performance metrics, compatibility

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of `just` recipes in the justfile are documented in the runbook with examples within 1 week of feature completion.
- **SC-002**: Operators can resolve 80% of common startup/memory issues using only the troubleshooting guide without additional support.
- **SC-003**: Model profile selection accuracy improves to 95% (correct profile chosen for given memory tier) using the decision tree.
- **SC-004**: New operators can complete server startup and model selection tasks in under 5 minutes using the runbook.
- **SC-005**: Runbook reduces operational support requests related to server management command usage and profile selection by 50% within 1 month of release.

## Assumptions

- The project's justfile is the authoritative source for all server management command recipes.
- Troubleshooting scenarios are specific to Apple Silicon (M-series) systems running local MLX inference servers.
- Model profiles are pre-defined in the project's configuration and align with 48GB, 64GB, and 96GB memory tiers.
- Operators have basic familiarity with command-line interfaces and system monitoring tools.
