# Feature Specification: Per-Path Hybrid Quantization

**Feature Branch**: `007-hybrid-quantization`  
**Created**: 2026-05-20  
**Status**: Draft  
**Input**: User description: "Create per-path hybrid quantization spec - Implement 3-bit attention / 2-bit expert configuration (tq3a-tq2e g32), Add support for latent-MoE architectures (Nemotron-3-Super-120B-A12B), Design calibration-data Lloyd-Max codebook option (Phase 2 from research), Reference: sharpner/turboquant-mlx V3 Lloyd-Max implementation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure Per-Path Hybrid Quantization (Priority: P1)

As a system operator running large language models on Apple Silicon with memory constraints, I want to configure per-path hybrid quantization settings so that I can optimize memory usage while maintaining model quality for 120B+ parameter models.

**Why this priority**: This is the core functionality that enables memory-efficient serving of large models. Without per-path configuration, users cannot take advantage of specialized quantization strategies for different model components.

**Independent Test**: Can be fully tested by configuring a model with tq3a-tq2e g32 quantization settings and verifying the model loads with the correct bit allocation per path (attention layers at 3-bit, expert layers at 2-bit, group size 32).

**Acceptance Scenarios**:

1. **Given** a model configuration file, **When** a user specifies `tq3a-tq2e g32` quantization preset, **Then** the system applies 3-bit quantization to attention layers, 2-bit quantization to expert layers, with group size 32
2. **Given** a running server instance, **When** a model with per-path quantization is loaded, **Then** the system reports the correct quantization configuration in health/status endpoints
3. **Given** limited memory conditions, **When** using per-path hybrid quantization, **Then** the model uses less memory than uniform 4-bit quantization while maintaining comparable output quality

---

### User Story 2 - Support Latent-MoE Architectures (Priority: P2)

As a system operator deploying Nemotron-3-Super-120B-A12B or similar latent-MoE architectures, I want the quantization system to properly handle mixture-of-experts layer structures so that I can serve these models efficiently on memory-constrained Apple Silicon systems.

**Why this priority**: Latent-MoE architectures represent a significant class of large models. Supporting them expands the system's capability to serve state-of-the-art models with sparse activation patterns.

**Independent Test**: Can be fully tested by loading a Nemotron-3-Super-120B-A12B model and verifying that expert layers are correctly identified and quantized according to the per-path configuration.

**Acceptance Scenarios**:

1. **Given** a Nemotron-3-Super-120B-A12B model, **When** the model is loaded with hybrid quantization, **Then** expert layers are detected and quantized at 2-bit precision while attention layers use 3-bit
2. **Given** a latent-MoE model configuration, **When** the system processes the model architecture, **Then** it correctly identifies expert routing layers and applies appropriate quantization
3. **Given** a model with sparse expert activation, **When** inference is performed, **Then** only the active experts are loaded into memory with correct quantization

---

### User Story 3 - Configure Lloyd-Max Codebook Calibration (Priority: P3)

As a system operator optimizing quantization quality, I want to use Lloyd-Max codebook calibration with calibration data so that I can achieve better quantization accuracy compared to standard quantization methods.

**Why this priority**: Lloyd-Max codebook optimization is a research-phase feature that provides quality improvements. While valuable, it's not required for basic operation and can be added after core quantization works.

**Independent Test**: Can be fully tested by providing calibration data and verifying that the system generates optimized Lloyd-Max codebooks that improve quantization accuracy metrics.

**Acceptance Scenarios**:

1. **Given** calibration data in supported format, **When** Lloyd-Max codebook option is enabled, **Then** the system processes calibration data to generate optimized quantization codebooks
2. **Given** a model with Lloyd-Max optimized codebooks, **When** the model is quantized, **Then** output quality metrics show improvement over standard quantization
3. **Given** the V3 Lloyd-Max implementation from sharpner/turboquant-mlx, **When** calibration is performed, **Then** the system follows the referenced algorithm for codebook generation

---

### Edge Cases

- What happens when a model architecture doesn't have clear attention/expert layer separation?
- How does the system handle models that don't support the requested bit configuration (e.g., very small models)?
- What occurs when calibration data is provided but Lloyd-Max is disabled?
- How does the system behave when memory is insufficient even with hybrid quantization?
- What happens when switching between different quantization presets for the same model?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support per-path quantization configuration allowing different bit widths for attention layers versus expert layers
- **FR-002**: System MUST implement `tq3a-tq2e g32` preset that applies 3-bit quantization to attention paths, 2-bit quantization to expert paths, with group size 32
- **FR-003**: System MUST detect and properly handle latent-MoE architectures including Nemotron-3-Super-120B-A12B with 12B active parameters
- **FR-004**: System MUST identify expert layers in mixture-of-experts models and apply expert-specific quantization settings
- **FR-005**: System MUST support Lloyd-Max codebook calibration using provided calibration data for improved quantization accuracy
- **FR-006**: System MUST reference and implement V3 Lloyd-Max algorithm as described in sharpner/turboquant-mlx research
- **FR-007**: System MUST validate quantization configurations before applying them to ensure compatibility with target model architecture
- **FR-008**: System MUST report current quantization configuration through server health/status endpoints
- **FR-009**: System MUST maintain OpenAI-compatible API behavior when serving models with hybrid quantization
- **FR-010**: System MUST preserve model output quality within acceptable bounds when using per-path hybrid quantization compared to full-precision baselines

### Key Entities *(include if feature involves data)*

- **QuantizationProfile**: Configuration specifying bit-width per model path (attention, expert, other layers), group size, and calibration method
- **ModelArchitecture**: Representation of model structure including layer types, expert counts, and activation patterns for latent-MoE models
- **CalibrationDataset**: Collection of sample data used for Lloyd-Max codebook optimization with metadata about source and format
- **Codebook**: Optimized quantization lookup tables generated from calibration data using Lloyd-Max algorithm

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Models with 120B+ parameters can be loaded and served on Apple Silicon systems with 48GB memory using per-path hybrid quantization
- **SC-002**: Memory usage for Nemotron-3-Super-120B-A12B with tq3a-tq2e g32 is reduced by at least 40% compared to full-precision (16-bit) while maintaining output quality within 5% of baseline on standard benchmarks
- **SC-003**: Server startup time for hybrid-quantized models does not exceed 150% of startup time for uniformly quantized models of equivalent size
- **SC-004**: Token generation rate for hybrid-quantized 120B models meets or exceeds 20 tokens per second on Apple Silicon with 48GB memory
- **SC-005**: Lloyd-Max codebook calibration improves quantization accuracy by at least 10% (measured by perplexity reduction) compared to standard quantization without calibration data
- **SC-006**: System correctly identifies and quantizes expert layers in latent-MoE architectures with 99%+ accuracy in layer classification
- **SC-007**: All quantization configurations are validated within 5 seconds before model loading begins
- **SC-008**: Server health endpoints accurately report quantization configuration with 100% correctness for all active models

## Assumptions

- The sharpner/turboquant-mlx V3 implementation provides a reference algorithm that can be adapted for MLX integration
- Latent-MoE architectures follow detectable patterns for expert layer identification (specific layer naming or structural signatures)
- Calibration data for Lloyd-Max optimization is provided in formats compatible with MLX tensor operations
- Apple Silicon memory constraints are the primary driver for quantization decisions (48GB unified memory systems)
- The mlx_lm.server OpenAI-compatible API remains the serving layer that benefits from these quantization improvements
- Group size 32 provides optimal balance between memory savings and quantization accuracy for the target model class
