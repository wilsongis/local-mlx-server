# Feature Specification: Admin GUI MVP

**Feature Branch**: `009-admin-gui-mvp`

**Created**: 2026-05-24

**Status**: Draft

**Input**: User description: "ADMIN-001 Admin GUI MVP with just command integration for immediate server visibility and control"

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.

  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - View server status and basic controls (Priority: P1)

As an administrator, I want to see whether the MLX server is currently running and be able to start or stop it via a simple interface, so that I can manage server availability without using the command line.

**Why this priority**: This is the core value proposition: immediate visibility and control. Without this, the GUI provides no MVP value.

**Independent Test**: Can be fully tested by checking server status indicator and verifying start/stop buttons trigger the corresponding `just` commands, delivering immediate server control value.

**Acceptance Scenarios**:

1. **Given** the server is not running, **When** I open the admin GUI, **Then** I see a clear "Stopped" status indicator and a "Start Server" button.
2. **Given** the server is running, **When** I open the admin GUI, **Then** I see a "Running" status indicator and a "Stop Server" button.
3. **Given** I click "Start Server", **When** the server starts successfully, **Then** the status changes to "Running" and the button changes to "Stop Server".
4. **Given** I click "Stop Server", **When** the server stops successfully, **Then** the status changes to "Stopped" and the button changes to "Start Server".

---

### User Story 2 - View current model information (Priority: P2)

As an administrator, I want to see which model is currently loaded (if any) and its basic details, so that I know what the server is serving without inspecting configuration files.

**Why this priority**: Model visibility is important for verification and debugging, but secondary to server control.

**Independent Test**: Can be fully tested by displaying model name and maybe quantization info after server starts, delivering model awareness value.

**Acceptance Scenarios**:

1. **Given** the server is running with a model loaded, **When** I view the admin GUI, **Then** I see the model name and quantization configuration (e.g., "llama-3-120b-4bit").
2. **Given** the server is stopped, **When** I view the admin GUI, **Then** I see "No model loaded" or similar indication.

---

### User Story 3 - View server logs or recent activity (Priority: P3)

As an administrator, I want to see recent server logs or activity messages, so that I can quickly diagnose issues without accessing log files directly.

**Why this priority**: Helpful for troubleshooting but not essential for basic control; can be added after core visibility/control.

**Independent Test**: Can be fully tested by displaying a scrolling log panel that shows recent stdout/stderr from the server process, delivering diagnostic value.

**Acceptance Scenarios**:

1. **Given** the server has produced log output, **When** I view the admin GUI, **Then** I see the last N lines of log output in a readable format.
2. **Given** the server is stopped, **When** I view the admin GUI, **Then** I see a message indicating no logs are available.

---

### Edge Cases

- What happens when the `just` command fails to execute (e.g., permission denied, command not found)? The GUI should display an error message.
- How does the GUI handle the server crashing unexpectedly? The status should reflect the actual state (maybe via periodic health check).
- What if multiple administrators access the GUI simultaneously? For MVP, assume single-user local access; concurrent access is out of scope.
- How does the GUI detect server status if the server was started outside the GUI? The GUI should query the actual process status, not rely on internal state.

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST display server running status (running/stopped) in a clear visual indicator.
- **FR-002**: System MUST provide controls to start and stop the server via `just` command integration (e.g., `just start`, `just stop`).
- **FR-003**: System MUST display currently loaded model name and quantization configuration when server is running.
- **FR-004**: System MUST execute `just` commands for server control and capture their success/failure.
- **FR-005**: System MUST refresh status periodically (e.g., every 5 seconds) or on demand by polling the MLX server's HTTP health endpoint (default: `http://localhost:8000/health`, configurable) to reflect current state.
- **FR-006**: System MUST display error messages when a `just` command fails, including the reason if available.
- **FR-007**: System MUST be accessible via a web browser on localhost (or equivalent local interface) without requiring network access.
- **FR-008**: System MUST have a minimal, clean interface suitable for quick administrative checks.

### Key Entities *(include if feature involves data)*

- **Server Status**: Represents the current state of the MLX server (running, stopped, unknown). Attributes: status, timestamp of last check.
- **Model Info**: Represents the model currently served. Attributes: name, quantization config, maybe path.
- **Log Entry**: Represents a line of log output. Attributes: timestamp, message, level (info, error, etc.).

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: Administrator can determine server running status within 5 seconds of opening the GUI.
- **SC-002**: Administrator can start or stop the server with at most 2 clicks from the GUI.
- **SC-003**: Server status displayed in the GUI matches actual server state with at least 95% accuracy (allowing for minor delay).
- **SC-004**: Administrator can identify the currently loaded model within 10 seconds of viewing the GUI.
- **SC-005**: GUI loads and becomes interactive within 3 seconds on the target hardware.

## Assumptions

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right assumptions based on reasonable defaults
  chosen when the feature description did not specify certain details.
-->

- The admin GUI will be a locally accessible interface that the administrator can access through standard means (e.g., web browser).
- The GUI will integrate with `just` commands by invoking them via Python subprocess calls from a Flask or FastAPI backend. The backend component is considered part of the GUI MVP but can be a separate module. The GUI server will listen on port 8080 by default.
- The MVP focuses on visibility and control for a single local MLX server instance; multi-server management is out of scope.
- The GUI is intended for local use only (localhost), not exposed to external networks.
- The `just` commands referenced (start, stop, etc.) are assumed to exist in the project's `justfile`. If they don't, the GUI should gracefully handle missing commands.
- Log viewing is limited to recent output and does not include persistent log storage.
- The GUI does not require authentication for MVP, as it is intended for local single-user scenarios.
- The project's rule about web UI being in a separate directory boundary will be respected: the GUI code will reside in a `gui/` directory at the repository root, clearly separated from core infrastructure code.

## Clarifications

### Session 2026-05-24

- Q: What technology stack should the Admin GUI MVP use? → A: Python backend (Flask/FastAPI) + server-rendered HTML templates (minimal JS)
- Q: On which port should the Admin GUI server listen? → A: 8080
- Q: How should the GUI detect MLX server status? → A: HTTP health endpoint polling (query MLX server's `/health`)
- Q: Where should the Admin GUI code reside within the repository? → A: `gui/` directory at repository root
- Q: What is the default MLX server port that the GUI should poll for health status? → A: 8000
