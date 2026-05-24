# Local MLX Server - Project TODO

> All tasks are designed to be implemented via `/speckit.*` commands (specify → plan → tasks → implement → verify).
> Operational workflows use `just` recipes as the stable interface.

---

## 📋 Spec-Driven Development Pipeline

### Documentation & Constitution Specs
- [x] **DOC-001** (COMPLETED - Documentation Consolidation): Create project documentation spec via `/speckit.specify`
  - Consolidate README.md, AGENTS.md, and constitution into unified documentation structure
  - Define documentation standards for inference infrastructure projects
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [x] **DOC-002**: Create security implementation spec via `/speckit.specify`
  - Define security boundaries for local inference server
  - Document API endpoint security considerations (mlx_lm.server OpenAI compatibility)
  - Specify secure model path handling and environment variable management
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [x] **DOC-003**: Create operations runbook spec via `/speckit.specify`
  - Document all `just` recipes with examples and edge cases
  - Create troubleshooting guide for common startup/memory issues
  - Define model profile selection decision tree (48GB vs 64GB vs 96GB tiers)
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

---

## 🔧 Infrastructure & Server Specs

### Core Server Infrastructure
- [x] **INFRA-001** (COMPLETED - MLX Server Wrapper): Create mlx_lm.server wrapper spec via `/speckit.specify`
  - Design startup/shutdown workflow with health checks
  - Implement model profile selection logic (per-path hybrid quantization support)
  - Add startup argument presets for 120B+ model memory optimization
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [x] **INFRA-002** (COMPLETED - Server Lifecycle Management): Create server lifecycle management spec via `/speckit.specify`
  - Design `just` recipes: `server-start`, `server-stop`, `server-status`
  - Implement PID file management and port conflict resolution
  - Add graceful shutdown with active request draining
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [x] **INFRA-003** (COMPLETED - Model Management): Create model management spec via `/speckit.specify`
  - Design `just` recipes: `models-list`, `model-use <profile>`
  - Implement model profile registry (Nemotron-120B-48GB, GPT-OSS-120B, Qwen3.5-122B)
  - Add model path validation and disk space checks
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

---

## ⚡ TurboQuant & Quantization Specs

### Weight Compression
- [x] **QUANT-001**: Create per-path hybrid quantization spec via `/speckit.specify`
  - Implement 3-bit attention / 2-bit expert configuration (tq3a-tq2e g32)
  - Add support for latent-MoE architectures (Nemotron-3-Super-120B-A12B)
  - Design calibration-data Lloyd-Max codebook option (Phase 2 from research)
  - Reference: [sharpner/turboquant-mlx](https://github.com/sharpner/turboquant-mlx) V3 Lloyd-Max implementation
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **QUANT-002**: Create KV cache compression spec via `/speckit.specify`
  - Implement TurboQuant V2 (speed) and V3 (quality) paths for KV cache compression
  - **V2 path**: Use `mx.quantized_matmul` (Metal-accelerated), 3.6x compression at ~105% FP16 speed
  - **V3 path**: Lloyd-Max codebook (paper-correct), 4.1-5.5x compression, requires custom Metal kernels for speed
  - Add hybrid attention support (KVCache, RotatingKVCache, ArraysCache)
  - Design double-compression rules (3-bit weights + 4-bit KV for ~20B, 3-bit+3-bit for 100B+)
  - **Key finding**: V2 3-bit rot+QJL beats FP16 on Gemma (D=256) by 1.1%, acts as regularizer
  - Reference: [sharpner/turboquant-mlx](https://github.com/sharpner/turboquant-mlx), [arozanov/turboquant-mlx](https://github.com/arozanov/turboquant-mlx) for fused kernels
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **QUANT-003**: Create quantization CLI integration spec via `/speckit.specify`
  - Wrap `turboquant-convert` with sensible defaults for Apple Silicon
  - Add `bits_for_path()` hook for custom per-path bit allocation
  - Implement model card generation with compression metadata
  - Add head_dim-aware defaults: D=256 models (Gemma) get better low-bit quality than D=128 (Llama)
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **QUANT-004**: Create model size estimation tool spec via `/speckit.specify`
  - Implement compression ratio calculator (4.8-6.6x for weights, 3.8-4.6x for KV cache)
  - Add peak memory estimator (on-disk + KV cache + 5-8 GB overhead)
  - Design per-path hybrid quantization size predictor (tq3a-tq2e g32)
  - Add CLI integration: `just estimate-model <model> --bits --attn-bits --mlp-bits --context`
  - Include double-compression rules (3-bit+4-bit for ~20B, 3-bit+3-bit for 100B+)
  - Account for head_dim scaling: D=256 models achieve 5.5x KV compression at +7% PPL vs +27% for D=128
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

---

## 🧪 Testing & Validation Specs

### Benchmark & Stress Testing
- [ ] **TEST-001**: Create stress test harness spec via `/speckit.specify`
  - Implement 6-test harness from research (prose, arithmetic, code, long-context, formatting, long-output)
  - Add perplexity benchmarking across model sizes (1B to 122B)
  - Design regression detection for quantization quality
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **TEST-002**: Create memory profiling spec via `/speckit.specify`
  - Implement peak memory tracking (`mx.metal.get_active_memory()`)
  - Add memory budget validation (40.8 GB peak for 48GB Mac, 52 GB for 64GB)
  - Design OOM detection with graceful fallback suggestions
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **TEST-003**: Create inference speed benchmarking spec via `/speckit.specify`
  - Benchmark tokens/sec across model configurations
  - Add Metal kernel performance regression tests
  - Design chunked-launch wrapper validation for long contexts
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

---

## 🛡️ Security Specs

### Security Implementation
- [ ] **SEC-001**: Create API security spec via `/speckit.specify`
  - Define authentication/authorization for local server (if needed)
  - Document CORS and network binding considerations for mlx_lm.server
  - Add rate limiting and request size validation
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **SEC-002**: Create model path security spec via `/speckit.specify`
  - Validate model paths against directory traversal attacks
  - Implement safe model download from HuggingFace
  - Add checksum verification for downloaded models
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **SEC-003**: Create environment security spec via `/speckit.specify`
  - Secure handling of `.env` files and API keys
  - Validate `just` recipe safety (no arbitrary command execution)
  - Add pre-commit hooks for secret scanning (via `.pre-commit-config.yaml`)
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

---

## 🔄 Dependency & Environment Specs

### UV & Package Management
- [ ] **DEPS-001**: Create dependency management spec via `/speckit.specify`
  - Pin MLX and TurboQuant versions for reproducibility
  - Design uv.lock update workflow with compatibility testing
  - Add Python version compatibility matrix (3.11+ for Apple Silicon)
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **DEPS-002**: Create Containerfile optimization spec via `/speckit.specify`
  - Minimize container image size while supporting TurboQuant Metal kernels
  - Add multi-stage build for PyPI package compilation
  - Design containerized test workflow
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **DEPS-003**: Create offline dependency bundle spec via `/speckit.specify`
  - Build reproducible offline wheelhouse for MLX/TurboQuant stack (`uv export` + wheel cache)
  - Add `just deps-bundle` and `just deps-install-offline` recipes for air-gapped recovery
  - Validate install path with network disabled on clean Apple Silicon environment
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

---

## 🧭 Offline Reliability & Runtime Policy Specs

### Critical Offline Productivity
- [ ] **OFFLINE-001**: Create offline model artifact mirror spec via `/speckit.specify`
  - Define local mirror layout for model weights, tokenizer files, and model cards
  - Add `just models-mirror` and `just models-verify` recipes with checksums/manifests
  - Validate cold-start recovery when internet is unavailable
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **OFFLINE-002**: Create startup preflight and degraded-mode spec via `/speckit.specify`
  - Add preflight checks for memory budget, wired-limit constraints, disk space, and dependency integrity
  - Implement deterministic fallback profile selection when target profile exceeds available memory
  - Add `just preflight` and `just preflight-offline` recipes for repeatable launch validation
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **OFFLINE-003**: Create local runbook snapshot spec via `/speckit.specify`
  - Persist last-known-good runtime settings (profile, sampler, cache bits, context)
  - Add `just runbook-snapshot` and `just runbook-restore` for fast offline recovery
  - Capture failure fingerprints (OOM, Metal memory faults, kernel dispatch errors) with remediation hints
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

### Runtime Quantization Policy
- [ ] **QUANT-005**: Create runtime policy engine spec via `/speckit.specify`
  - Encode prompt-aware sampler rules (numeric prompts disable repetition penalty)
  - Enforce model-scale KV policy (small models: 4-bit KV on 3-bit weights; 100B+: 3-bit KV)
  - Add profile-safe defaults for `min_tokens` on think-enabled models to avoid premature EOS
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **QUANT-006**: Create KV compatibility hardening spec via `/speckit.specify`
  - Validate prompt-first cache conversion pipeline before generation begins
  - Add compatibility checks for attention sinks and hybrid cache types (KVCache/RotatingKVCache/ArraysCache)
  - Add explicit fallback behavior when quantized SDPA paths are incompatible
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

---

## 📊 Monitoring & Observability Specs

### Server Monitoring
- [ ] **OBS-001**: Create server health checks spec via `/speckit.specify`
  - Implement `/health` endpoint with model loading status
  - Add GPU memory usage reporting via Metal APIs
  - Design request logging with token throughput metrics
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **OBS-002**: Create operational dashboards spec via `/speckit.specify`
  - Design text-based dashboard for `just server-status`
  - Add model performance summary (tokens/sec, memory, quantization config)
  - Implement alerting for memory pressure conditions
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **OBS-003**: Create offline incident telemetry spec via `/speckit.specify`
  - Capture structured local telemetry for OOM, wired-limit, and kernel dispatch failures
  - Add rolling benchmark deltas for tokens/sec, peak memory, and quality checks per profile
  - Expose `just incidents-tail` and `just incidents-report` for offline triage
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

---

## 🚀 Future Enhancements (Phase 2/3)

### Advanced Features
- [ ] **FUTURE-001**: Create calibrated codebook spec via `/speckit.specify` (Phase 2 from research)
  - Implement activation-based Lloyd-Max codebook training
  - Add `--calibration-source` flag to convert.py
  - Design per-layer codebook optimization
  - Reference: V3 Lloyd-Max outperforms affine at 3-bit: +5-9% vs +9-23% PPL
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **FUTURE-002**: Create fused QJL kernel spec via `/speckit.specify` (Phase 2 from research)
  - Implement 1-bit residual correction for V2 paths (QJL works as additional correction, not replacement)
  - Add Metal kernel for fused QJL sign-bit scoring (see `turboquant/fused_qjl.py` in sharpner/turboquant-mlx)
  - Design fallback to unfused path when kernel unavailable
  - **Key finding**: QJL improves V2 3-bit from +6.6% to +5.3% PPL, but TurboQuant_prod (replacing MSE bits) degrades quality
  - Reference: [arozanov/turboquant-mlx](https://github.com/arozanov/turboquant-mlx) achieves 4.6x compression at 98% FP16 speed with fused kernels
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **FUTURE-003**: Create automatic bit-width search spec via `/speckit.specify` (Phase 3 from research)
  - Design calibration-loss-based bit-width policy search
  - Add `bits_for_path()` auto-tuning from validation set
  - Implement Pareto-optimal bit-width curves (quality vs memory)
  - Account for head_dim: D=256 models (Gemma) tolerate lower bits than D=128 (Llama)
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **FUTURE-004**: Create incremental KV dequantization spec via `/speckit.specify`
  - Cache dequantized segments and process only newly appended tokens to reduce per-step overhead
  - Benchmark memory/speed tradeoff on 20B, 32B, 120B, and 122B profiles
  - Define fallback to full-step dequantization when memory headroom is low
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **FUTURE-005**: Create embedding quantization spec via `/speckit.specify`
  - Quantize embedding/output layers with quality guardrails for smaller models
  - Measure size-quality impact for 1B-7B where embeddings dominate footprint
  - Add selective opt-out for models that regress on instruction-following quality
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **FUTURE-006**: Create external quantizer parity benchmark spec via `/speckit.specify`
  - Run controlled comparisons vs GPTQ and AWQ on MoE and dense models
  - Report quality/speed/memory/cost curves with identical prompts and context lengths
  - Add publishable benchmark template for repeatable future comparisons
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

---

## ✅ Completed Tasks

- **INFRA-002** (Server Lifecycle Management): All 42 tasks completed in `specs/005-server-lifecycle-management/tasks.md`. Implemented `scripts/server-lifecycle.py` with PID management, port conflict resolution, graceful shutdown, and `just` recipes (`server-start`, `server-stop`, `server-status`). Verified with `tests/test_server_lifecycle.py`.

- **INFRA-003** (Model Management): Implemented via spec 006-model-management. Created `scripts/model-management.py` (435 lines) with `ModelRegistry`, `ModelProfile`, `ValidationResult` classes, state file management with `flock` locking, and CLI commands. Added `just` recipes: `models-list`, `model-use`, `model-status`. Configured three model profiles in `scripts/wrapper-config/profiles.yaml` (nemotron-120b, gpt-oss-120b, qwen3.5-122b).

*(Tasks will be moved here as they are completed via `/speckit.verify`)*

---

## 📝 Notes

- All specs should reference the research papers in `docs/research/` for technical context
- Constitution principles in `.specify/memory/constitution.md` must be respected
- Operational workflows MUST use `just` recipes, not ad-hoc shell commands
- All changes must preserve OpenAI-compatible API behavior via mlx_lm.server
- Priority is 120B+ model viability on Apple Silicon memory-constrained systems

---

*Generated from project documentation and research papers on 2026-05-04*
