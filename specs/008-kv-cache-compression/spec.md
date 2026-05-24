# Feature Specification: KV Cache Compression

**Feature Branch**: `008-kv-cache-compression`

**Created**: 2026-05-21

**Status**: Draft

**Input**: User description: "QUANT-002: Create KV cache compression spec via `/speckit.specify` - Implement TurboQuant V2 (speed) and V3 (quality) paths for KV cache compression - V2 path: Use `mx.quantized_matmul` (Metal-accelerated), 3.6x compression at ~105% FP16 speed - V3 path: Lloyd-Max codebook (paper-correct), 4.1-5.5x compression, requires custom Metal kernels for speed - Add hybrid attention support (KVCache, RotatingKVCache, ArraysCache) - Design double-compression rules (3-bit weights + 4-bit KV for ~20B, 3-bit+3-bit for 100B+) - Key finding: V2 3-bit rot+QJL beats FP16 on Gemma (D=256) by 1.1%, acts as regularizer - Reference: sharpner/turboquant-mlx, arozanov/turboquant-mlx for fused kernels"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run Larger Models with Less Memory (Priority: P1)

Infrastructure operators running local LLM inference need to serve models with larger context windows or larger parameter counts within fixed memory constraints. By compressing the key-value cache that accumulates during text generation, operators can reduce memory usage by 3-5x, enabling 120B+ parameter models to run on 48GB Apple Silicon systems with extended context lengths.

**Why this priority**: Memory is the primary constraint for local inference on Apple Silicon. KV cache compression directly enables larger models and longer contexts within fixed hardware limits, delivering immediate value to users trying to maximize their hardware utilization.

**Independent Test**: Can be fully tested by measuring memory usage before and after enabling KV cache compression with a fixed model and context length, and verifying that memory usage decreases by the expected compression ratio while maintaining output quality.

**Acceptance Scenarios**:

1. **Given** a 120B parameter model loaded on a 48GB MacBook, **When** KV cache compression is enabled, **Then** memory usage for the KV cache is reduced by at least 3x compared to uncompressed FP16
2. **Given** KV cache compression is active, **When** generating text with a 4096 token context, **Then** output quality (measured by perplexity or task accuracy) remains within 1.5% of uncompressed baseline
3. **Given** a model is loaded, **When** switching between compressed and uncompressed modes, **Then** the transition completes without server restart and subsequent generations use the selected mode

---

### User Story 2 - Choose Speed-Optimized Compression (Priority: P2)

Operators who prioritize inference speed over maximum compression can select a speed-optimized compression path that uses Metal-accelerated operations to achieve ~3.6x compression while maintaining ~105% of FP16 inference speed. This path is ideal for interactive use cases where responsiveness matters more than fitting the absolute largest context.

**Why this priority**: Many users prefer slightly less compression in exchange for faster inference, especially for interactive chat scenarios. This provides a practical tradeoff option.

**Independent Test**: Can be fully tested by enabling the speed-optimized compression path and measuring tokens-per-second throughput compared to uncompressed baseline, verifying it meets or exceeds FP16 speed.

**Acceptance Scenarios**:

1. **Given** the speed-optimized compression path is selected, **When** generating text, **Then** inference speed is at least 100% of uncompressed FP16 baseline
2. **Given** speed-optimized compression is active, **When** processing a 2048 token context, **Then** KV cache memory usage is reduced by at least 3x
3. **Given** a batch of requests, **When** using speed-optimized compression, **Then** the Metal accelerator is utilized for quantization operations without falling back to CPU

---

### User Story 3 - Choose Quality-Optimized Compression (Priority: P2)

Operators who need maximum memory reduction with minimal quality loss can select a quality-optimized compression path using advanced quantization techniques that achieve 4.1-5.5x compression. This path is ideal for serving the largest possible models or longest contexts where memory is the binding constraint.

**Why this priority**: For users at the absolute memory limit trying to serve 120B+ models, maximum compression is essential even at some computational cost.

**Independent Test**: Can be fully tested by enabling the quality-optimized compression path and verifying that compression ratios of 4x+ are achieved while quality remains within acceptable bounds (within 2% of FP16).

**Acceptance Scenarios**:

1. **Given** the quality-optimized compression path is selected, **When** compressing a KV cache for a 120B model, **Then** memory usage is reduced by at least 4x compared to FP16
2. **Given** quality-optimized compression is active, **When** evaluating output on standard benchmarks, **Then** accuracy is within 2% of uncompressed baseline
3. **Given** custom Metal kernels are available, **When** using quality-optimized compression, **Then** inference speed degradation is minimized compared to a CPU-only implementation

---

### User Story 4 - Automatic Compression Strategy Selection (Priority: P3)

Operators with different model sizes can benefit from automatic compression strategy selection based on model scale. For ~20B models, a balanced strategy (3-bit weights + 4-bit KV) is optimal, while for 100B+ models, aggressive double-compression (3-bit weights + 3-bit KV) maximizes viability on memory-constrained systems.

**Why this priority**: Automatic optimization reduces configuration burden and ensures users get the best results for their specific model without manual tuning.

**Independent Test**: Can be fully tested by loading models of different sizes and verifying that the system automatically selects and applies the appropriate compression strategy for each model size class.

**Acceptance Scenarios**:

1. **Given** a ~20B parameter model is loaded, **When** automatic compression is enabled, **Then** the system selects 3-bit weight quantization with 4-bit KV cache compression
2. **Given** a 100B+ parameter model is loaded, **When** automatic compression is enabled, **Then** the system selects 3-bit weight quantization with 3-bit KV cache compression
3. **Given** automatic strategy is active, **When** switching between different sized models, **Then** the compression strategy updates appropriately without manual reconfiguration

---

### Edge Cases

- What happens when KV cache compression is enabled but the model or hardware doesn't support the required operations?
- How does the system handle switching compression modes mid-session with existing cached tokens?
- What is the fallback behavior when custom Metal kernels fail to load for the quality-optimized path?
- How does compression interact with different attention cache types (standard KVCache, rotating caches, array-based caches)?
- What happens when memory savings from compression allow context extension beyond the model's trained context window?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support at least two selectable KV cache compression paths: speed-optimized and quality-optimized
- **FR-002**: System MUST achieve minimum 3x KV cache memory reduction for speed-optimized compression path
- **FR-003**: System MUST achieve minimum 4x KV cache memory reduction for quality-optimized compression path
- **FR-004**: System MUST maintain output quality within 2% of uncompressed FP16 baseline for both compression paths
- **FR-005**: System MUST support speed-optimized compression at ≥100% of uncompressed FP16 inference speed
- **FR-006**: System MUST provide hybrid attention support compatible with KVCache, RotatingKVCache, and ArraysCache implementations
- **FR-007**: System MUST automatically select compression strategy based on model size when configured to do so
- **FR-008**: System MUST support double-compression configurations (combined weight and KV cache compression)
- **FR-009**: System MUST allow runtime switching between compression modes without server restart
- **FR-010**: System MUST provide fallback to uncompressed mode if compression initialization fails

## Key Entities *(include if feature involves data)*

- **Compression Profile**: A named configuration specifying compression path (V2/V3), bit-width for KV cache, and associated kernel requirements
- **Model Size Class**: Categorization of models (e.g., ~20B, ~70B, 100B+) used to determine optimal compression strategy
- **Attention Cache Type**: The underlying cache implementation (KVCache, RotatingKVCache, ArraysCache) that must be compatible with the selected compression method

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can reduce KV cache memory usage by 3-5x depending on selected compression path
- **SC-002**: Inference speed with speed-optimized compression is at least equal to uncompressed FP16 baseline
- **SC-003**: Output quality with either compression path is within 2% of uncompressed baseline on standard language modeling benchmarks
- **SC-004**: 120B+ parameter models become viable on 48GB Apple Silicon systems when using aggressive double-compression
- **SC-005**: Compression mode switching completes in under 5 seconds without requiring server restart
- **SC-006**: System supports all three major attention cache types (KVCache, RotatingKVCache, ArraysCache) with compression enabled

## Assumptions

- Operators are familiar with basic quantization concepts and tradeoffs between memory, speed, and quality
- Apple Silicon Metal acceleration is available and functional on the target hardware
- The underlying MLX framework supports the required quantized matrix multiplication operations
- Custom Metal kernels for the quality-optimized path can be compiled and loaded at runtime
- Model weights are already quantized using a compatible scheme (e.g., 3-bit) when using double-compression
- The existing hybrid quantization infrastructure (from spec 007) provides the foundation for weight quantization components
- Benchmark datasets for measuring output quality are available and representative of real-world usage
- Operators will test compression paths with their specific models before deploying to production workloads
