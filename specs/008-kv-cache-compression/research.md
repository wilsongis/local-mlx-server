# Research: KV Cache Compression for Local MLX Server

## Decision Log

### Decision: KV Cache Compression Implementation Approach
**Decision**: Integrate TurboQuant V2 (speed-optimized) and V3 (quality-optimized) KV cache compression paths, referencing `manjunathshiva/turboquant-mlx` implementation
**Rationale**: The spec requires two selectable compression paths. TurboQuant V2 uses Metal-accelerated `mx.quantized_matmul` for ~3.6x compression at ~105% FP16 speed. V3 uses Lloyd-Max codebook quantization for 4.1-5.5x compression. The `turboquant-mlx` package provides working implementations for MLX that we can adapt and integrate with our existing `scripts/quantization/` infrastructure from spec 007.
**Alternatives considered**:
- MLX built-in `kv_bits` parameter: Limited to basic quantization, doesn't support V2/V3 paths or Lloyd-Max optimization
- Custom from-scratch implementation: High risk, TurboQuant implementations already available and tested
- Integrate via `turboquant-mlx` PyPI package directly: Less control, harder to customize for our infrastructure needs

### Decision: Hybrid Attention Cache Compatibility Strategy
**Decision**: Detect cache type per-layer and apply compression only to `KVCache` instances; pass `RotatingKVCache` and `ArraysCache` through unchanged
**Rationale**: Research shows GPT-OSS uses `KVCache` (full-attention) and `RotatingKVCache` (sliding-window); Qwen3.5 uses `KVCache` and `ArraysCache` (linear-attention). Compression only applies to growing caches. Following the pattern from `turboquant-mlx`: `convert_cache_to_turboquant()` function inspects each cache instance and skips non-`KVCache` types.
**Alternatives considered**:
- Uniform compression across all cache types: Incompatible with sliding-window and linear-attention semantics
- Modify MLX cache implementations: Violates "Reversible, Testable Changes" principle, high maintenance burden
- Separate compression configs per layer: Over-engineering, cache type detection is sufficient

### Decision: Prompt-First Conversion Pattern
**Decision**: Process entire prompt with full-precision `KVCache`, then convert to compressed format before generation begins
**Rationale**: Research confirms this pattern (also used by MLX's built-in `kv_bits`): prompt processing benefits from exact KV values for establishing attention patterns. Subsequent generation tokens are compressed on arrival. This matches the spec requirement for "runtime switching between compression modes without server restart" - conversion happens once after prompt processing.
**Alternatives considered**:
- Compress prompt KV immediately: Degrades initial attention pattern establishment
- Always use compressed format: Loses prompt processing quality for no benefit (prompt is one-time cost)

### Decision: Double-Compression Strategy Selection
**Decision**: Implement automatic strategy based on model size: 4-bit KV for ~20B models with 3-bit weights; 3-bit KV for 100B+ models with 3-bit weights
**Rationale**: Research shows compounding quantization noise affects small models more. GPT-OSS-20B fails with 3-bit weights + 3-bit KV (repetition collapse within 30 tokens). GPT-OSS-120B and Qwen3.5-122B run cleanly with 3-bit+3-bit. The Central Limit Theorem approximation requires sufficient dimensionality (8+ KV heads). Rule: "3-bit KV for FP16-weight models at every scale; 4-bit KV on small models (~20B) with compressed weights, 3-bit KV on 100B+ with compressed weights."
**Alternatives considered**:
- Always use 4-bit KV with compressed weights: Wastes memory on 100B+ models where 3-bit works fine
- Always use 3-bit KV: Breaks small models with compressed weights
- Manual configuration only: Violates spec FR-007 (automatic selection based on model size)

### Decision: Attention Sinks Compatibility
**Decision**: Return float16 dequantized values and route through standard `mx.fast.scaled_dot_product_attention` path, NOT the quantized attention path
**Rationale**: GPT-OSS uses learned attention sink vectors. MLX's quantized attention path (`quantized_scaled_dot_product_attention`) explicitly rejects sinks with `ValueError`. Research shows dequantizing to float16 for attention computation is compatible with all attention features (sinks, sliding windows, causal masks). Memory savings come from compressed *storage*, not computation.
**Alternatives considered**:
- Use quantized attention path: Crashes on GPT-OSS and potentially other models with sinks
- Modify sink handling: Too invasive, dequant approach works universally

### Decision: Metal Kernel Integration for V3 Path
**Decision**: Reference `sharpner/turboquant-mlx` V3 implementation for custom Metal kernel compilation and loading; provide fallback to CPU path if kernels fail to load
**Rationale**: V3 (quality-optimized) path requires custom Metal kernels for speed. The `turboquant-mlx` package builds Metal extensions on install. We need to implement similar kernel compilation/loading with graceful fallback to CPU implementation if Metal acceleration unavailable. This satisfies FR-010 (fallback to uncompressed if initialization fails).
**Alternatives considered**:
- V3 CPU-only implementation: Too slow for practical use
- Skip V3 path entirely: Violates spec requirement for quality-optimized path
- Require pre-compiled kernels: Inflexible, breaks portability

## Best Practices Research

### KV Cache Compression Profiles
- **V2 (Speed-optimized)**: Use `mx.quantized_matmul` for Metal-accelerated operations, target 3.6x compression at ≥100% FP16 speed
- **V3 (Quality-optimized)**: Lloyd-Max codebook quantization with per-group RMS normalization and Hadamard rotation, target 4.1-5.5x compression
- **Bit-width selection**: 3-bit is sweet spot (0.98+ cosine similarity, 4.6x compression); 4-bit for double-compression on small models; 2-bit degrades quality
- **Group size**: 64 elements per group (from research), store per-group float16 scale factors

### Compression Ratio Calculations
- **3-bit compression**: 4.6x for KV cache (pack 3-bit indices into uint32, plus float16 scales)
- **4-bit compression**: 3.8x for KV cache
- **Memory savings at scale**: GPT-OSS-120B at 131K context saves 7.4 GB (9.2 GB FP16 → 1.8 GB TQ 3-bit)
- **Speed flip**: On 120B+ models, compression *increases* tok/s (less memory bandwidth); on 20B models, compression is 3x slower due to dequant overhead

### Integration with mlx_lm.server
- **Cache conversion point**: After prompt processing, before generation loop starts
- **Conversion function**: `convert_cache_to_turboquant(prompt_cache, tq_bits=3, group_size=64)`
- **Detection logic**: Check `isinstance(cache, KVCache)` to identify compressible caches
- **State management**: Cache object replacement in model's cache list, maintain offset and other metadata

### Hybrid Attention Cache Types
- **KVCache**: Standard full-attention cache, grows linearly with context → compressible
- **RotatingKVCache**: Sliding-window attention, fixed size (e.g., 128 tokens) → skip compression
- **ArraysCache**: Linear-attention (e.g., GatedDeltaNet), different semantics → skip compression
- **Detection**: `from mlx_lm.models.cache import KVCache, RotatingKVCache, ArraysCache`

### Double-Compression Interaction with Spec 007
- **Weight quantization**: Use existing `QuantizationManager` and `config_builder.py` from spec 007
- **KV compression**: New `KVCacheCompressionManager` in `scripts/quantization/`
- **Combined config**: Extend `profiles.yaml` schema with `kv_cache` section (bits, group_size, path selection)
- **Model size detection**: Reuse `model_detector.py` patterns from spec 007 to categorize models (~20B, ~70B, 100B+)

## Technical Context Resolved

All NEEDS CLARIFICATION items from Technical Context have been resolved:
- ✅ Language/Version: Python 3.11+ (from existing project, MLX compatibility)
- ✅ Primary Dependencies: `turboquant-mlx` (reference implementation), `mlx-lm` (existing), custom Metal kernels for V3
- ✅ Storage: N/A (runtime memory optimization)
- ✅ Testing: pytest (existing framework, add `tests/test_kv_cache_compression.py`)
- ✅ Target Platform: macOS/Apple Silicon (Metal acceleration required for V2/V3)
- ✅ Project Type: Infrastructure enhancement (extends `scripts/quantization/`)
- ✅ Performance Goals: V2 ≥100% FP16 speed, 3.6x compression; V3 4.1-5.5x compression; switching <5s; 120B+ viable on 48GB
- ✅ Constraints: Preserve `mlx_lm.server` API, Metal acceleration, hybrid attention support, fallback behavior
- ✅ Scale/Scope: 2-3 new Python modules, just recipe extensions, integration with spec 007 infrastructure

## Research References

- **TurboQuant Paper**: [arXiv:2504.19874](https://arxiv.org/abs/2504.19874) - Original Google research on weight and KV cache compression
- **TurboQuant-MLX GitHub**: [manjunathshiva/turboquant-mlx](https://github.com/manjunathshiva/turboquant-mlx) - MLX implementation with KV cache support
- **TurboQuant-MLX PyPI**: [turboquant-mlx-full](https://pypi.org/project/turboquant-mlx-full) - Installable package with Metal kernels
- **Research Article**: "TurboQuant: Compressing KV cache 4x on Apple Silicon" - Practical implementation details and benchmarks
- **Spec 007 (Hybrid Quantization)**: Existing weight quantization infrastructure we'll build upon
