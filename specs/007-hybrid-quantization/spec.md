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
4. **Given** a full-precision (16-bit) baseline model, **When** per-path hybrid quantization (e.g., tq3a-tq2e g32) is applied, **Then** output quality (measured by perplexity on standard benchmarks like WikiText-2) is within 5% of the full-precision baseline, satisfying FR-010.

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

**Why this priority**: Lloyd-Max codebook optimization is a research-phase feature that provides quality improvements. While valuable, it's not required for basic operation (SHOULD-level requirement) and can be added after core quantization works.

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
- **FR-005**: System SHOULD support Lloyd-Max codebook calibration using provided calibration data for improved quantization accuracy
- **FR-006**: System SHOULD reference and implement V3 Lloyd-Max algorithm as described in sharpner/turboquant-mlx research
- **FR-007**: System MUST validate quantization configurations before applying them to ensure compatibility with target model architecture
- **FR-008**: System MUST report current quantization configuration through server health/status endpoints
- **FR-009**: System MUST maintain OpenAI-compatible API behavior when serving models with hybrid quantization
- **FR-010**: System MUST preserve model output quality within acceptable bounds when using per-path hybrid quantization compared to full-precision baselines

### Non-Functional Requirements

- **NFR-001 (Reliability)**: System MUST validate model checksum before applying quantization to ensure model integrity
- **NFR-002 (Security)**: Calibration data MUST be handled securely with proper file permission validation and path traversal protection
- **NFR-003 (Reliability)**: Quantization configuration files MUST be validated for syntax errors before model loading with clear error messages
- **NFR-004 (Security)**: System MUST verify model source authenticity through checksum verification before quantization
- **NFR-005 (Reliability)**: Failed quantization attempts MUST NOT leave partial model state; rollback to previous configuration on failure
- **NFR-006 (Observability)**: System MUST log quantization operations with sufficient detail for debugging (configuration applied, layers quantized, errors encountered)

### Error Handling

System MUST return specific error responses for the following conditions:

- **ERR-001 (Invalid Bit-Width)**: When `attention_bits` or `expert_bits` is outside 2-8 range, return error: `"Invalid bit-width: {value}. Must be between 2 and 8."` with HTTP 400
- **ERR-002 (Unsupported Model Architecture)**: When model architecture cannot be determined or does not match known patterns, return error: `"Unsupported model architecture: {model_name}. Cannot identify layer types for per-path quantization."` with HTTP 422
- **ERR-003 (Calibration Data Format Error)**: When calibration data format is not supported (not JSON/numpy/text), return error: `"Invalid calibration data format: {format}. Supported formats: JSON, numpy, text."` with HTTP 400
- **ERR-004 (Checksum Mismatch)**: When model file checksum does not match expected value, return error: `"Model integrity check failed. Checksum mismatch detected."` with HTTP 422
- **ERR-005 (Insufficient Memory)**: When memory is insufficient for requested quantization configuration, return error: `"Insufficient memory for quantization configuration. Required: {required}MB, Available: {available}MB."` with HTTP 507
- **ERR-006 (Invalid Group Size)**: When `group_size` is not one of [16, 32, 64, 128], return error: `"Invalid group size: {value}. Must be one of: 16, 32, 64, 128."` with HTTP 400

### Key Entities *(include if feature involves data)*

- **QuantizationProfile** (YAML format): Configuration specifying bit-width per model path
  - `version`: string (semver, e.g., "1.0.0")
  - `attention_bits`: integer (2-8, default: 3)
  - `expert_bits`: integer (2-8, default: 2)
  - `group_size`: integer (16, 32, 64, 128; default: 32)
  - `calibration_method`: string (enum: "none", "lloyd-max"; default: "none")
  - `model_patterns`: array of strings (regex patterns for model architecture detection)
  - `preset_name`: string (optional, e.g., "tq3a-tq2e-g32")

- **ModelArchitecture** (in-memory representation): Model structure including layer types
  - `architecture_name`: string (e.g., "Nemotron-3-Super-120B-A12B")
  - `total_params`: integer (total parameter count)
  - `active_params`: integer (active parameters for MoE models)
  - `layer_types`: array of strings (e.g., ["attention", "mlp", "expert_router", "expert_0", ...])
  - `expert_count`: integer (number of experts, 0 for non-MoE)
  - `is_moe`: boolean (true for mixture-of-experts architectures)

- **CalibrationDataset** (JSON metadata + numpy arrays): Sample data for Lloyd-Max optimization
  - `dataset_id`: string (UUID)
  - `source`: string (origin description)
  - `format`: string (enum: "json", "numpy", "text")
  - `sample_count`: integer (number of calibration samples)
  - `data_path`: string (filesystem path to calibration data)
  - `created_at`: string (ISO 8601 timestamp)

- **Codebook** (binary MLX format): Optimized quantization lookup tables
  - `codebook_id`: string (UUID)
  - `algorithm_version`: string (e.g., "V3")
  - `bits`: integer (quantization bit-width this codebook applies to)
  - `group_size`: integer (group size used for this codebook)
  - `model_layers`: array of strings (which layers this codebook applies to)
  - `binary_path`: string (path to serialized MLX array file)
  - `generated_at`: string (ISO 8601 timestamp)

## Integration Points

The per-path hybrid quantization feature integrates with the following system components:

### mlx_lm.server CLI Integration
- **CLI Argument**: `--quant-config <path>` - Path to QuantizationProfile YAML file
- **CLI Argument**: `--calibration-data <path>` - Path to CalibrationDataset for Lloyd-Max optimization
- **Environment Variable**: `MLX_QUANT_PROFILE` - Alternative to CLI arg for specifying quantization profile
- **Server Startup**: Quantization is applied during model load before server starts accepting requests
- **Health Endpoint**: Extend `/health` response with `quantization` object containing current config

### just Command Recipes
New recipes to be added to `justfile`:
- `just quant-apply <model> <profile>` - Apply quantization profile to specified model
- `just quant-validate <profile>` - Validate quantization profile syntax and compatibility
- `just quant-list` - List available quantization profiles in `scripts/wrapper-config/profiles.yaml`
- `just quant-calibrate <dataset> <output>` - Run Lloyd-Max calibration with provided dataset
- `just quant-status` - Show current quantization status for active model

### profiles.yaml Integration
Quantization profiles stored in `scripts/wrapper-config/profiles.yaml`:
```yaml
quantization_profiles:
  tq3a-tq2e-g32:
    attention_bits: 3
    expert_bits: 2
    group_size: 32
    calibration_method: none
    model_patterns:
      - ".*nemotron.*120b.*"
      - ".*120b.*moe.*"
  
  tq4a-tq4e-g32:
    attention_bits: 4
    expert_bits: 4
    group_size: 32
    calibration_method: none
    model_patterns: []
```

### Model Management Integration
- Extends `scripts/model-management.py` with quantization profile storage in model metadata
- Model download/load commands accept optional `--quant-profile` parameter
- Active model symlink (`.active-model`) can reference quantized model variants

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Models with 120B+ parameters can be loaded and served on Apple Silicon systems with 48GB memory using per-path hybrid quantization
- **SC-002**: Memory usage for Nemotron-3-Super-120B-A12B with tq3a-tq2e g32 is reduced by at least 40% compared to full-precision (16-bit) while maintaining output quality within 5% of full-precision baseline (validating FR-010) and within 5% of uniform 4-bit baseline on standard benchmarks
- **SC-003**: Server startup time for hybrid-quantized models does not exceed 150% of startup time for uniformly quantized models of equivalent size
- **SC-004**: Token generation rate for hybrid-quantized 120B models meets or exceeds 20 tokens per second on Apple Silicon with 48GB memory
- **SC-005**: Lloyd-Max codebook calibration improves quantization accuracy by at least 10% (measured by perplexity reduction) compared to standard quantization without calibration data, and by at least 5% compared to full-precision baselines for supported models.
- **SC-006**: System correctly identifies and quantizes expert layers in latent-MoE architectures with 99%+ accuracy in layer classification
- **SC-007**: All quantization configurations are validated within 5 seconds before model loading begins
- **SC-008**: Server health endpoints accurately report quantization configuration with 100% correctness for all active models
- **SC-009**: Output quality of hybrid-quantized models is within 5% of full-precision (16-bit) baselines on standard benchmarks (e.g., WikiText-2 perplexity), directly validating FR-010.
- **SC-010**: All error conditions (ERR-001 to ERR-006) are validated with automated tests, ensuring correct error messages and HTTP status codes are returned.
- **SC-011**: Non-functional requirements (NFR-001 to NFR-006) are validated, including checksum verification, secure calibration data handling, failed quantization rollback, and detailed operation logging.

## Assumptions

- The sharpner/turboquant-mlx V3 implementation provides a reference algorithm that can be adapted for MLX integration
- Latent-MoE architectures follow detectable patterns for expert layer identification (specific layer naming or structural signatures)
- Calibration data for Lloyd-Max optimization is provided in formats compatible with MLX tensor operations
- Apple Silicon memory constraints are the primary driver for quantization decisions (48GB unified memory systems)
- The mlx_lm.server OpenAI-compatible API remains the serving layer that benefits from these quantization improvements
- Group size 32 provides optimal balance between memory savings and quantization accuracy for the target model class

## Clarifications

### Session 2026-05-20

- Q: What should be explicitly defined as out-of-scope for this feature? → A: No runtime quantization changes, no non-MLX backends, no sub-2-bit quantization
- Q: What non-functional requirements should be added? → A: Reliability & security: model checksum validation, secure calibration data handling, config syntax validation
- Q: What data format specifications should be defined for entities? → A: QuantizationProfile (YAML), CalibrationDataset (JSON/numpy), Codebook (binary MLX) with field types
- Q: What error handling definitions are needed? → A: Invalid bit-width, unsupported model, calibration format error, checksum mismatch errors
- Q: What integration points should be defined? → A: mlx_lm.server CLI args, just command recipes, profiles.yaml quant profile storage

## Out of Scope

The following items are explicitly **out of scope** for this feature:

- **Runtime quantization changes**: Quantization configuration cannot be changed while a model is loaded; server restart required
- **Non-MLX backends**: Only MLX framework is supported; PyTorch, TensorFlow, and other backends are not supported
- **Sub-2-bit quantization**: Minimum bit-width supported is 2-bit; 1-bit or lower quantization is not implemented
- **Model training or fine-tuning**: This feature is inference-only; no training capabilities are included
- **Multi-device or distributed inference**: Single-device Apple Silicon configurations only; no multi-GPU or cluster support
- **Dynamic expert routing optimization**: Expert routing logic is handled by the model architecture; no custom routing optimizations are implemented
