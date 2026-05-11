# Feature Specification: MLX Server Wrapper

**Feature Branch**: `004-mlx-server-wrapper`  
**Created**: 2026-05-07  
**Status**: Draft  
**Input**: User description: "Create mlx_lm.server wrapper spec via `/speckit.specify` - Design startup/shutdown workflow with health checks, Implement model profile selection logic (per-path hybrid quantization support), Add startup argument presets for 120B+ model memory optimization"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start MLX Server with Health Monitoring (Priority: P1)

Infrastructure operators need to start the mlx_lm.server with automated health checks so they can ensure the local inference server is running reliably and can detect failures quickly.

**Why this priority**: Server startup and health monitoring are foundational - without a running, healthy server, no inference can occur. This is the core operational workflow.

**Independent Test**: Can be fully tested by starting the server and verifying health check endpoints return expected status, delivering immediate operational value.

**Acceptance Scenarios**:

1. **Given** the server is not running, **When** operator executes startup command, **Then** the mlx_lm.server starts with configured model and returns ready status
2. **Given** the server is running, **When** health check is invoked, **Then** system returns healthy status with model loaded confirmation
3. **Given** the server is running, **When** a shutdown signal is received, **Then** server performs graceful shutdown releasing memory and model resources
4. **Given** the server fails to start, **When** startup is attempted, **Then** system returns clear error message indicating failure reason

---

### User Story 2 - Model Profile Selection with Hybrid Quantization (Priority: P2)

Infrastructure operators need to select model profiles that support per-path hybrid quantization so they can optimize memory usage for different model architectures and serving requirements.

**Why this priority**: Profile selection enables flexible deployment configurations. Hybrid quantization is critical for 120B+ models on memory-constrained Apple Silicon systems.

**Independent Test**: Can be fully tested by selecting different model profiles and verifying the correct quantization configuration is applied per model path.

**Acceptance Scenarios**:

1. **Given** multiple model profiles are defined, **When** operator selects a profile, **Then** system loads the corresponding model with specified quantization settings
2. **Given** a profile specifies hybrid quantization, **When** model loads, **Then** different layers use configured quantization types per path
3. **Given** an invalid profile name, **When** operator attempts selection, **Then** system returns error listing available profiles
4. **Given** per-path quantization is configured, **When** model initializes, **Then** KV cache uses compression settings matching the quantization profile

---

### User Story 3 - 120B+ Model Memory Optimization Presets (Priority: P2)

Infrastructure operators need startup argument presets for 120B+ models so they can reliably serve large models on Apple Silicon with constrained memory.

**Why this priority**: Memory optimization for 120B+ models is a primary use case for this infrastructure. Presets reduce configuration errors and ensure viable serving.

**Independent Test**: Can be fully tested by starting server with 120B+ preset and verifying memory usage stays within available bounds while maintaining inference capability.

**Acceptance Scenarios**:

1. **Given** a 120B+ model preset is selected, **When** server starts, **Then** inference arguments are optimized for memory-constrained serving (reduced context, optimized batch size, quantized KV cache)
2. **Given** available memory is insufficient, **When** preset is applied, **Then** system warns operator and suggests alternative presets
3. **Given** multiple presets are available, **When** operator lists presets, **Then** system displays preset names with memory requirements and model size targets
4. **Given** custom arguments are provided with a preset, **When** server starts, **Then** preset defaults are overridden by explicit arguments

---

### Edge Cases

- What happens when server starts but model path is invalid or model files are corrupted?
- How does system handle health check timeouts when model loading exceeds expected time?
- What occurs when multiple server instances attempt to start on the same port?
- How does shutdown behave when active inference requests are in progress?
- What happens when memory pressure occurs during model loading with a 120B+ preset?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a startup workflow that initializes mlx_lm.server with configurable model path and server arguments
- **FR-002**: System MUST implement health check endpoint that reports server status, model loading state, and readiness for inference
- **FR-003**: System MUST support graceful shutdown that releases model resources and stops accepting new requests before termination
- **FR-004**: System MUST provide model profile selection mechanism that maps profile names to quantization and inference configurations
- **FR-005**: System MUST support per-path hybrid quantization configuration within model profiles (different quantization per model layer/path)
- **FR-006**: System MUST include startup argument presets targeting 120B+ model serving on Apple Silicon with memory constraints
- **FR-007**: System MUST validate model paths and profile selections before attempting server startup
- **FR-008**: System MUST display available profiles and presets when invalid selections are made
- **FR-009**: System MUST integrate with `just` command recipes for operational consistency (start, stop, status, health checks)
- **FR-010**: System MUST preserve OpenAI-compatible API behavior through mlx_lm.server configuration

### Key Entities *(include if feature involves data)*

- **Model Profile**: Configuration entity defining model path, quantization settings, KV cache compression, and inference arguments
- **Startup Preset**: Named configuration targeting specific model size classes (e.g., 120B+) with memory-optimized defaults
- **Health Status**: Runtime entity tracking server state (initializing, ready, degraded, shutdown) with model loading progress
- **Quantization Config**: Per-path settings defining layer-specific quantization types and compression parameters

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can start the MLX server and receive ready confirmation within 5 minutes for 120B+ models on 48GB systems
- **SC-002**: Health checks return status within 1 second when server is running
- **SC-003**: Server shutdown completes within 30 seconds, releasing all model memory
- **SC-004**: Model profile selection loads correct quantization settings in under 10 seconds for profile switching
- **SC-005**: 120B+ model presets enable successful inference with less than 48GB memory consumption on Apple Silicon
- **SC-006**: 95% of health check requests return accurate status (no false positives/negatives)
- **SC-007**: Operators can identify and select from at least 3 distinct model profiles or presets

## Assumptions

- mlx_lm.server is the underlying server technology providing OpenAI-compatible API endpoints
- Apple Silicon systems with 48GB unified memory are the primary deployment target for 120B+ models
- Hybrid quantization refers to using different quantization types (e.g., 4-bit, 8-bit) for different model layers or paths
- `just` command recipes are the preferred operational interface for server lifecycle management
- KV cache compression is a critical factor for serving large models with extended context windows
- TurboQuant may be used as the quantization framework for hybrid configurations
