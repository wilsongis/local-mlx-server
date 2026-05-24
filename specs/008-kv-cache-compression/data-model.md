# Data Model: KV Cache Compression

## Entities

### CompressionProfile
A named configuration specifying compression path, bit-width, and kernel requirements for KV cache compression.

| Field | Type | Description | Validation |
|-------|------|-------------|-------------|
| `name` | string | Profile identifier (e.g., "v2-speed", "v3-quality", "auto") | Required, unique within profiles.yaml |
| `path` | string | Compression path: "v2" (speed-optimized) or "v3" (quality-optimized) | Must be "v2" or "v3" |
| `bits` | integer | Bit-width for KV cache quantization (2, 3, or 4) | Must be 2, 3, or 4; 3 is recommended sweet spot |
| `group_size` | integer | Elements per group for RMS normalization | Default 64, must be power of 2 |
| `use_metal` | boolean | Whether to use Metal acceleration (V2 requires true, V3 optional) | V2: true; V3: true with fallback to CPU |
| `hadamard_rotation` | boolean | Apply Hadamard transform before quantization | Default true (recommended for quality) |
| `codebook_type` | string | Codebook method: "lloyd-max" (V3) or "uniform" (V2) | V2: "uniform"; V3: "lloyd-max" |
| `target_model_size` | string | Model size class this profile is optimized for ("20B", "70B", "100B+") | Used by "auto" profile for selection |

### ModelSizeClass
Categorization of models used to determine optimal compression strategy.

| Field | Type | Description | Validation |
|-------|------|-------------|-------------|
| `class_name` | string | Size class identifier ("20B", "70B", "100B+") | Must match known size classes |
| `weight_bits` | integer | Recommended weight quantization bits when using double-compression | 3 for all classes (from spec 007) |
| `kv_bits` | integer | Recommended KV cache bits for this model class | 4 for 20B, 3 for 100B+ (double-compression) |
| `min_memory_gb` | integer | Minimum system memory required | 48GB for 100B+ with double-compression |

### AttentionCacheType
Enumeration of MLX attention cache implementations that must be compatible with compression.

| Value | Description | Compressible |
|-------|-------------|--------------|
| `KVCache` | Standard full-attention cache, grows linearly with context | ✅ Yes |
| `RotatingKVCache` | Sliding-window attention, fixed size (e.g., 128 tokens) | ❌ No |
| `ArraysCache` | Linear-attention cache (e.g., GatedDeltaNet) | ❌ No |

## Relationships

```
CompressionProfile
    ↓ targets
ModelSizeClass (determines optimal profile via "auto" selection)
    ↓ applied to
Model (loaded via mlx_lm.load)
    ↓ produces
KVCache instances (one per layer)
    ↓ compressed by
TurboQuantKVCache (replaces KVCache for compressible layers)
```

## State Transitions

### Compression Mode Switching

```
[Uncompressed] -- enable(v2_profile) --> [V2-Compressed]
[Uncompressed] -- enable(v3_profile) --> [V3-Compressed]
[Uncompressed] -- enable(auto_profile) --> [Auto-Selected]
[V2-Compressed] -- switch(v3_profile) --> [V3-Compressed]
[V3-Compressed] -- switch(v2_profile) --> [V2-Compressed]
[V2-Compressed] -- disable() --> [Uncompressed]
[V3-Compressed] -- disable() --> [Uncompressed]
[Auto-Selected] -- model_change() --> [Auto-Selected] (re-evaluates)
```

**Transition Rules**:
1. Switching requires prompt re-processing with new cache type
2. Existing compressed cache is discarded on mode switch
3. Fallback to uncompressed on initialization failure (per FR-010)

## Validation Rules

### From Requirements (FR-001 to FR-010)

- **FR-002**: V2 profile must achieve ≥3x compression (validated by `bits=3` or `bits=4` with group_size)
- **FR-003**: V3 profile must achieve ≥4x compression (validated by `bits=3` with Lloyd-Max)
- **FR-004**: Output quality within 2% of FP16 (validated by `hadamard_rotation=true`, `codebook_type="lloyd-max"` for V3)
- **FR-005**: V2 must use `use_metal=true` for ≥100% FP16 speed
- **FR-006**: System must detect `AttentionCacheType` and skip non-KVCache instances
- **FR-007**: "auto" profile must check `ModelSizeClass` and select appropriate `kv_bits`
- **FR-008**: Double-compression config requires both `weight_bits` (from spec 007) and `kv_bits`
- **FR-009**: Mode switching via `convert_cache_to_turboquant()` after prompt processing
- **FR-010**: Initialization failure falls back to uncompressed `KVCache`

### Double-Compression Rules (from Research)

| Weight Bits | Model Size | KV Bits | Expected Result |
|-------------|-----------|---------|-----------------|
| 3 | ~20B | 4 | ✅ Clean output (4x KV savings) |
| 3 | ~20B | 3 | ❌ Repetition collapse (noise compounds) |
| 3 | 100B+ | 3 | ✅ Clean output (redundancy absorbs noise) |
| 3 | 100B+ | 4 | ✅ Clean output (conservative, slightly more memory) |
| FP16 | Any | 3 | ✅ Clean output (baseline, no weight noise) |

## Integration with Spec 007 (Hybrid Quantization)

The `CompressionProfile` extends the `QuantizationProfile` from spec 007:

```yaml
# In profiles.yaml
models:
  - name: "gpt-oss-120b"
    pattern: ".*gpt-oss.*120b.*"
    quantization:
      attention_bits: 3
      expert_bits: 2
      group_size: 32
    kv_cache:  # NEW: KV cache compression config
      profile: "auto"  # or "v2-speed", "v3-quality"
      bits: 3  # default, overridden by auto logic
      group_size: 64
```

The `QuantizationManager` (spec 007) and new `KVCacheCompressionManager` (spec 008) work together:
1. `QuantizationManager` handles weight quantization (attention/expert layers)
2. `KVCacheCompressionManager` handles KV cache compression
3. Double-compression tolerance checked at startup based on model size class
