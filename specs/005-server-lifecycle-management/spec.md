# Feature Specification: Server Lifecycle Management

**Feature Branch**: `005-server-lifecycle-management`  
**Created**: 2026-05-13  
**Status**: Draft  
**Input**: User description: "Create server lifecycle management spec via `/speckit.specify` - Design `just` recipes: `server-start`, `server-stop`, `server-status`, Implement PID file management and port conflict resolution, Add graceful shutdown with active request draining"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Server Start with PID Management (Priority: P1)

Infrastructure operators need to start the MLX server with PID file management so they can reliably track server processes, prevent duplicate starts, and detect stale PID files.

**Why this priority**: Server startup with proper PID management is foundational - operators need to know if a server is already running and prevent port conflicts before attempting to start a new instance.

**Independent Test**: Can be fully tested by starting the server, verifying PID file creation, attempting duplicate start (should fail), and checking PID file cleanup on shutdown.

**Acceptance Scenarios**:

1. **Given** the server is not running, **When** operator executes `just server-start`, **Then** the server starts and creates a PID file at configured location
2. **Given** a PID file exists from a previous run, **When** operator attempts `just server-start`, **Then** system checks if process is alive and removes stale PID file if dead
3. **Given** the server is already running, **When** operator attempts `just server-start`, **Then** system returns error indicating server already running with PID
4. **Given** port is already in use, **When** operator attempts `just server-start`, **Then** system detects port conflict and suggests available ports or terminates conflicting process

---

### User Story 2 - Server Stop with Graceful Shutdown (Priority: P1)

Infrastructure operators need to stop the server with graceful shutdown so they can drain active requests, release resources properly, and avoid interrupting in-progress inference.

**Why this priority**: Graceful shutdown is critical for production operations - abrupt termination can corrupt model state, lose active inference results, and leave resources locked.

**Independent Test**: Can be fully tested by starting server, initiating shutdown during active requests, and verifying requests complete before server terminates.

**Acceptance Scenarios**:

1. **Given** the server is running with active requests, **When** operator executes `just server-stop`, **Then** server stops accepting new requests and waits for active requests to complete before shutting down
2. **Given** the server is running, **When** operator executes `just server-stop`, **Then** system sends SIGTERM, waits for graceful period, then SIGKILL if process doesn't terminate
3. **Given** the server is running, **When** shutdown completes, **Then** PID file is removed and model resources are released
4. **Given** server is unresponsive to SIGTERM, **When** graceful period expires, **Then** system forces termination with SIGKILL and logs warning

---

### User Story 3 - Server Status Monitoring (Priority: P2)

Infrastructure operators need to check server status so they can quickly determine if the server is running, healthy, and accepting requests without manually checking processes or ports.

**Why this priority**: Status checking is a day-to-day operational need - operators need fast feedback on server state for monitoring and troubleshooting.

**Independent Test**: Can be fully tested by starting/stopping server and verifying `just server-status` returns accurate state information.

**Acceptance Scenarios**:

1. **Given** the server is running, **When** operator executes `just server-status`, **Then** system returns running status with PID, uptime, port, and health endpoint response
2. **Given** the server is not running, **When** operator executes `just server-status`, **Then** system returns stopped status and checks for stale PID files
3. **Given** the server is running but unresponsive, **When** operator executes `just server-status`, **Then** system returns degraded status indicating health check failure
4. **Given** multiple server instances are configured, **When** operator executes `just server-status`, **Then** system displays status for all configured instances

---

### User Story 4 - Port Conflict Resolution (Priority: P2)

Infrastructure operators need automatic port conflict detection and resolution so they can avoid manual port hunting and prevent startup failures when default port is occupied.

**Why this priority**: Port conflicts are common in development and testing environments - automated resolution reduces operational friction and manual debugging.

**Independent Test**: Can be fully tested by starting a process on the default port, then attempting server start and verifying conflict detection and resolution behavior.

**Acceptance Scenarios**:

1. **Given** default port is in use, **When** operator starts server, **Then** system detects conflict and offers to terminate conflicting process or use next available port
2. **Given** port conflict is detected, **When** operator chooses auto-assign, **Then** system finds next available port and updates configuration for current session
3. **Given** multiple ports are occupied, **When** system scans for availability, **Then** system checks a range of ports and reports all conflicts found
4. **Given** port is freed during startup, **When** conflict was transient, **Then** system retries binding and starts successfully

---

### Edge Cases

- What happens when PID file is corrupted or contains non-numeric content?
- How does system handle graceful shutdown timeout when active requests hang indefinitely?
- What occurs when server process crashes and PID file remains but process is dead?
- How does status check behave when health endpoint returns partial or malformed response?
- What happens when multiple operators attempt concurrent start/stop operations?
- How does port conflict resolution behave when conflicting process is owned by another user?
- What occurs when disk is full and PID file cannot be written during startup?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide `just server-start` recipe that starts MLX server with PID file creation and port conflict checking
- **FR-002**: System MUST provide `just server-stop` recipe that performs graceful shutdown with active request draining and configurable timeout
- **FR-003**: System MUST provide `just server-status` recipe that reports server state, PID, uptime, port, and health endpoint status
- **FR-004**: System MUST create PID file at configurable location (default: `/tmp/mlx-server.pid`) upon successful server startup
- **FR-005**: System MUST validate PID file on startup by checking if process is alive and remove stale PID files automatically
- **FR-006**: System MUST detect port conflicts before server startup and offer resolution options (terminate conflicting process or use alternate port)
- **FR-007**: System MUST implement graceful shutdown sequence: stop accepting new requests → wait for active requests to complete → release model resources → remove PID file
- **FR-008**: System MUST support configurable graceful shutdown timeout (default: 30 seconds) before forcing termination with SIGKILL
- **FR-009**: System MUST query health endpoint during status check to verify server is not just running but actually ready for inference
- **FR-010**: System MUST log all lifecycle events (start, stop, status checks, conflicts) to configured log destination

### Non-Functional Requirements

- **NFR-001**: Server start with PID management MUST complete within 5 seconds (excluding model loading time)
- **NFR-002**: Server status check MUST return results within 2 seconds even if health endpoint is slow
- **NFR-003**: Graceful shutdown MUST wait for active requests up to configured timeout but not block indefinitely
- **NFR-004**: PID file operations MUST use atomic writes to prevent corruption from concurrent access
- **NFR-005**: Port conflict detection MUST scan ports efficiently without excessive delay (max 1 second for scan)

## Success Metrics

- **SM-001**: `just server-start` successfully prevents duplicate starts and creates valid PID file in 100% of test cases
- **SM-002**: `just server-stop` completes graceful shutdown with active request draining in 95% of test cases within timeout
- **SM-003**: `just server-status` accurately reports server state (running/stopped/degraded) in 100% of test cases
- **SM-004**: Port conflict detection identifies and resolves conflicts in 90% of test cases without manual intervention
- **SM-005**: No stale PID files remain after server crash or unclean shutdown in 95% of test cases

## Dependencies

- **DEP-001**: [`justfile`](justfile) - Must be extended with `server-start`, `server-stop`, `server-status` recipes
- **DEP-002**: [`scripts/mlx_wrapper.py`](scripts/mlx_wrapper.py) - May need lifecycle management functions added
- **DEP-003**: `mlx_lm.server` - Health endpoint must be available for status checks
- **DEP-004**: POSIX `kill`, `lsof`/`ss` commands - Required for PID validation and port conflict detection

## Assumptions

- Operators have necessary permissions to terminate conflicting processes on ports they own
- Health endpoint at `/health` is available and returns status once model is loaded
- PID file location is writable by the user running the server
- Graceful shutdown timeout of 30 seconds is sufficient for most inference requests to complete
- Port scanning range (default 10 ports from configured port) is sufficient for finding available ports
