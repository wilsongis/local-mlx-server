# Feature Specification: Startup Preflight and Degraded Mode for Apple Silicon Local Serving

**Feature Branch**: `010-offline-002-startup`

**Created**: 2026-05-24

**Status**: Draft

**Input**: User description: "OFFLINE-002 Startup Preflight and Degraded Mode for Apple Silicon local serving"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Startup Preflight Validation (Priority: P1)

Before starting the local MLX server, the system runs automated preflight checks to verify Apple Silicon hardware and software readiness for serving large (120B+) models, preventing failed startup attempts and wasted system resources.

**Why this priority**: Critical to ensure the server only starts when it can reliably serve models, avoiding crashes or unstable operation that wastes time and memory on memory-constrained Apple Silicon systems.

**Independent Test**: Can be fully tested by triggering a server start attempt and verifying preflight checks execute and block startup if critical checks fail, delivering immediate value by preventing failed starts.

**Acceptance Scenarios**:

1. **Given** the system has sufficient GPU memory and valid MLX installation, **When** a user initiates server start, **Then** preflight checks pass and the server starts normally.
2. **Given** the system has insufficient GPU memory for the target 120B model, **When** a user initiates server start, **Then** preflight checks fail, startup is blocked, and the user receives a clear error message indicating insufficient memory.
3. **Given** MLX is not installed or is an incompatible version, **When** a user initiates server start, **Then** preflight checks fail and startup is blocked with a message to install/upgrade MLX.

---

### User Story 2 - Degraded Mode Operation (Priority: P2)

If non-critical preflight checks fail (e.g., optional optimizations like TurboQuant or KV cache compression are unavailable), the system enters a degraded mode where the server starts with reduced capabilities but still serves models at baseline functionality.

**Why this priority**: Balances reliability and usability—allows serving to proceed when non-essential features are missing, while clearly communicating reduced capabilities to the user.

**Independent Test**: Can be fully tested by simulating a failed non-critical check (e.g., missing TurboQuant) and verifying the server starts in degraded mode with core serving functionality intact.

**Acceptance Scenarios**:

1. **Given** TurboQuant dependencies are missing but core MLX is functional, **When** a user initiates server start, **Then** the system enters degraded mode, starts the server with standard quantization, and logs a degraded mode warning.
2. **Given** the system is in degraded mode, **When** a user queries the server health endpoint, **Then** the response indicates degraded status and lists unavailable features.
3. **Given** the system is in degraded mode, **When** a user sends an inference request, **Then** the request is processed successfully using baseline MLX serving capabilities.

---

### User Story 3 - Preflight and Degraded Mode Notification (Priority: P3)

Users receive clear, actionable feedback about preflight check results and degraded mode status via server logs, health endpoints, and the Admin GUI.

**Why this priority**: Ensures users understand why startup failed or why the system is in degraded mode, reducing debugging time and support requests.

**Independent Test**: Can be fully tested by checking log output, health endpoint responses, and Admin GUI status indicators after preflight checks or degraded mode activation.

**Acceptance Scenarios**:

1. **Given** preflight checks fail, **When** a user checks server logs, **Then** logs list all failed checks with clear descriptions and suggested fixes.
2. **Given** the system is in degraded mode, **When** a user opens the Admin GUI, **Then** a prominent warning banner displays degraded status and disabled features.
3. **Given** preflight checks pass with warnings, **When** a user queries the health endpoint, **Then** the response includes warning messages for non-critical issues.

---

### Edge Cases

- What happens when preflight checks pass but GPU memory is exhausted mid-inference? (System should return an out-of-memory error to the user without crashing)
- How does the system handle partial preflight check failures where some critical and some non-critical checks fail? (Block startup for critical failures, enter degraded mode only if all critical checks pass)
- What if the Admin GUI is unavailable when degraded mode activates? (Log warnings to server logs and health endpoint only)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST run preflight checks automatically before starting the MLX server.
- **FR-002**: Preflight checks MUST verify available GPU memory meets minimum requirements for the configured model (120B+ models require minimum 48GB unified memory for TurboQuant hybrid quantization, or 64GB for standard 4-bit quantization).
- **FR-003**: Preflight checks MUST validate MLX and core dependency versions are compatible with the target model.
- **FR-004**: Preflight checks MUST verify Apple Silicon GPU is available and functional.
- **FR-005**: System MUST block server startup if any critical preflight check fails.
- **FR-006**: System MUST enter degraded mode if non-critical preflight checks fail and all critical checks pass.
- **FR-007**: Degraded mode MUST disable non-essential features including: TurboQuant hybrid quantization, KV cache compression, and advanced profiling tools.
- **FR-008**: System MUST log all preflight check results (pass/fail, details) to server logs with timestamps.
- **FR-009**: System MUST expose preflight and degraded mode status via the existing server health endpoint.
- **FR-010**: System MUST notify the Admin GUI of degraded mode status for display to users.

### Key Entities

- **PreflightCheck**: Represents a single validation step, with attributes: name, type (critical/non-critical), status (pass/fail), details, timestamp.
- **DegradedModeConfig**: Configuration for degraded operation, with attributes: disabled features list, fallback quantization settings, status flag.
- **StartupAttempt**: Record of a server start attempt, with attributes: timestamp, preflight results, startup status (success/failed/degraded), error details.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of server start attempts execute preflight checks before starting the MLX server.
- **SC-002**: Preflight checks complete within 5 seconds on target hardware.
- **SC-003**: Server startup is blocked within 1 second of detecting a critical preflight failure.
- **SC-004**: Degraded mode activates within 2 seconds of detecting non-critical preflight failures, when critical checks pass.
- **SC-005**: 95% of users can successfully start the server in degraded mode when all critical preflight checks pass.
- **SC-006**: All preflight check results and degraded mode events are logged with timestamps and clear descriptions.
- **SC-007**: Health endpoint returns accurate preflight and degraded mode status within 100ms of a status change.

## Assumptions

- Target hardware is Apple Silicon M1/M2/M3 series devices with unified memory architecture.
- Critical preflight checks include: GPU memory availability, MLX installation validity, model path accessibility.
- Non-critical preflight checks include: TurboQuant availability, KV cache compression support, optional profiling tools.
- Degraded mode uses baseline MLX serving with standard 4-bit quantization for 120B+ models.
- The existing Admin GUI (in `gui/` directory) will be used to display degraded mode status.
- The existing health endpoint (part of `mlx_lm.server`) will be extended to include preflight and degraded mode status.
- Users have basic familiarity with server logs and health endpoints for troubleshooting.
