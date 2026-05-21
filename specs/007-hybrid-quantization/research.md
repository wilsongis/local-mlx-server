# Research: Per-Path Hybrid Quantization for Local MLX Server

## Decision Log

### Decision: Per-Path Quantization Implementation Approach
**Decision**: Extend `scripts/wrapper-config/profiles.yaml` with quantization profile schema and integrate with `mlx_lm.server` via `--quant-config` CLI argument
**Rationale**: The spec requires per-path quantization (different bit-widths for attention vs expert layers). MLX supports quantization configuration via YAML files passed to `mlx_lm.server --quant-config`. This approach leverages existing MLX infrastructure without creating custom quantization code. The `profiles.yaml` already stores model configurations, making it the natural location for quantization profiles.
**Alternatives considered**:
- Custom Python quantization wrapper: Would duplicate MLX's built-in quantization, high maintenance burden
- Hard-coded quantization in `mlx_wrapper.py`: Not configurable, violates "Reversible, Testable Changes" principle
- Separate quantization config file per model: More complex than extending existing `profiles.yaml`

### Decision: Latent-MoE Architecture Detection Strategy
**Decision**: Use regex pattern matching on model name/path (stored in `QuantizationProfile.model_patterns`) combined with layer inspection during model load
**Rationale**: The spec shows `model_patterns` in profiles (e.g., `".*nemotron.*120b.*"`). For Nemotron-3-Super-120B-A12B, we can detect the architecture from model name patterns. During model load, we can inspect layer types to identify expert layers (looking for "expert", "router", "MoE" in layer names). This two-phase approach (pattern pre-match + layer inspection) provides robust detection.
**Alternatives considered**:
- Pure layer inspection: Slower, requires model loading before detection
- Pure pattern matching: Fragile, model naming inconsistent across repositories
- External model registry: Over-engineering, requires maintenance of model database

### Decision: Lloyd-Max Codebook Calibration Implementation
**Decision**: Reference `sharpner/turboquant-mlx` V3 implementation; create `scripts/quantization/lloyd_max.py` module for calibration
**Rationale**: The spec explicitly references `sharpner/turboquant-mlx` V3 Lloyd-Max implementation. Rather than reimplementing, we should adapt their algorithm. Creating a dedicated module keeps quantization logic separate from server infrastructure. Calibration data input supports JSON, numpy, and text formats per spec requirements.
**Alternatives considered**:
- Integrate directly into `mlx_wrapper.py`: Violates separation of concerns
- Use MLX's built-in quantization only: Doesn't support Lloyd-Max optimization
- Implement from research papers: High risk, V3 implementation already available

### Decision: Health Endpoint Extension for Quantization Status
**Decision**: Extend `/health` endpoint in `scripts/server-lifecycle.py` to include `quantization` object with current config
**Rationale**: Spec requires "System MUST report current quantization configuration through server health/status endpoints" (FR-008). The existing `server-lifecycle.py` manages server state. Adding quantization status to health response maintains consistency with existing infrastructure.
**Alternatives considered**:
- Separate `/quant-status` endpoint: Adds complexity, not required by spec
- Environment variables: Not visible via API, violates "Local Serving Reliability" principle
- Log-only reporting: Not accessible to API clients

### Decision: Just Recipes for Quantization Operations
**Decision**: Add 5 new just recipes: `quant-apply`, `quant-validate`, `quant-list`, `quant-calibrate`, `quant-status`
**Rationale**: Constitution Principle IV mandates "Just Command Bridge". The spec explicitly lists these recipes in "Integration Points > just Command Recipes". Each recipe maps to a specific operational need: applying profiles, validation, listing, calibration, and status checking.
**Alternatives considered**:
- Python CLI script: Less discoverable than just recipes
- Direct `mlx_lm.server` commands: Not scripted, violates "operational workflows must be expressed through just recipes"
- Makefile targets: Project standardized on just

## Best Practices Research

### Quantization Profile Configuration
- **Schema validation**: Use JSON Schema or PyYAML validation to ensure required fields present
- **Default values**: Provide sensible defaults (attention_bits: 3, expert_bits: 2, group_size: 32)
- **Preset support**: Allow `preset_name` field to reference predefined configurations like "tq3a-tq2e-g32"
- **Model pattern matching**: Support regex patterns for automatic profile selection based on model name

### Latent-MoE Layer Detection
- **Layer naming conventions**: Look for layers containing "expert", "router", "MoE", "switch" in model's `config.json` or layer inspection
- **Expert count extraction**: Parse model config for `num_experts` or `n_experts` fields
- **Active parameter calculation**: For MoE models, identify `active_params` (e.g., 12B for Nemotron-3-Super-120B-A12B)

### Lloyd-Max Codebook Generation
- **Calibration data format**: Support JSON (tokenized text), numpy arrays (pre-tokenized), and plain text
- **Codebook storage**: Binary MLX format for efficient loading, store in `scripts/wrapper-config/codebooks/`
- **V3 algorithm**: Implement iterative Lloyd-Max with convergence threshold, reference `sharpner/turboquant-mlx`

### Integration with mlx_lm.server
- **CLI argument**: Use `--quant-config <path>` to pass quantization profile to server
- **Environment variable**: Support `MLX_QUANT_PROFILE` as alternative to CLI arg
- **Startup validation**: Validate quantization config before model load, fail fast with clear error messages

## Technical Context Resolved

All NEEDS CLARIFICATION items from Technical Context have been resolved:
- ✅ Language/Version: Python 3.11+ (from existing project, MLX compatibility)
- ✅ Primary Dependencies: mlx-lm, mlx, PyYAML, numpy (identified in spec and research)
- ✅ Storage: YAML profiles in `scripts/wrapper-config/profiles.yaml`, binary codebooks on filesystem
- ✅ Testing: pytest (existing framework in `tests/`)
- ✅ Target Platform: macOS on Apple Silicon (existing, spec focuses on 48GB systems)
- ✅ Project Type: Infrastructure/cli (quantization config management, just recipes)
- ✅ Performance Goals: 120B+ models on 48GB, 20+ tok/s, <150% startup time (from spec SC-001 to SC-004)
- ✅ Constraints: Memory-constrained (48GB unified), OpenAI-compatible API preservation, reversible config (from spec and constitution)
- ✅ Scale/Scope: 5 just recipes, 1-2 Python modules extended, YAML profile schema, health endpoint extension (from spec integration points)
