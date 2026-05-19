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

- [ ] **INFRA-002**: Create server lifecycle management spec via `/speckit.specify`
  - Design `just` recipes: `server-start`, `server-stop`, `server-status`
  - Implement PID file management and port conflict resolution
  - Add graceful shutdown with active request draining
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **INFRA-003**: Create model management spec via `/speckit.specify`
  - Design `just` recipes: `models-list`, `model-use <profile>`
  - Implement model profile registry (Nemotron-120B-48GB, GPT-OSS-120B, Qwen3.5-122B)
  - Add model path validation and disk space checks
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

---

## ⚡ TurboQuant & Quantization Specs

### Weight Compression
- [ ] **QUANT-001**: Create per-path hybrid quantization spec via `/speckit.specify`
  - Implement 3-bit attention / 2-bit expert configuration (tq3a-tq2e g32)
  - Add support for latent-MoE architectures (Nemotron-3-Super-120B-A12B)
  - Design calibration-data Lloyd-Max codebook option (Phase 2 from research)
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **QUANT-002**: Create KV cache compression spec via `/speckit.specify`
  - Implement 3-bit/4-bit KV cache compression with TurboQuant
  - Add hybrid attention support (KVCache, RotatingKVCache, ArraysCache)
  - Design double-compression rules (3-bit weights + 4-bit KV for ~20B, 3-bit+3-bit for 100B+)
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **QUANT-003**: Create quantization CLI integration spec via `/speckit.specify`
  - Wrap `turboquant-convert` with sensible defaults for Apple Silicon
  - Add `bits_for_path()` hook for custom per-path bit allocation
  - Implement model card generation with compression metadata
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **QUANT-004**: Create model size estimation tool spec via `/speckit.specify`
  - Implement compression ratio calculator (4.8-6.6x for weights, 3.8-4.6x for KV cache)
  - Add peak memory estimator (on-disk + KV cache + 5-8 GB overhead)
  - Design per-path hybrid quantization size predictor (tq3a-tq2e g32)
  - Add CLI integration: `just estimate-model <model> --bits --attn-bits --mlp-bits --context`
  - Include double-compression rules (3-bit+4-bit for ~20B, 3-bit+3-bit for 100B+)
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

---

## 🚀 Future Enhancements (Phase 2/3)

### Advanced Features
- [ ] **FUTURE-001**: Create calibrated codebook spec via `/speckit.specify` (Phase 2 from research)
  - Implement activation-based Lloyd-Max codebook training
  - Add `--calibration-source` flag to convert.py
  - Design per-layer codebook optimization
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **FUTURE-002**: Create fused QJL kernel spec via `/speckit.specify` (Phase 2 from research)
  - Implement 1-bit residual correction for SwitchLinear paths
  - Add Metal kernel for fused QJL in MoE layers
  - Design fallback to unfused path when kernel unavailable
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

- [ ] **FUTURE-003**: Create automatic bit-width search spec via `/speckit.specify` (Phase 3 from research)
  - Design calibration-loss-based bit-width policy search
  - Add `bits_for_path()` auto-tuning from validation set
  - Implement Pareto-optimal bit-width curves (quality vs memory)
  - Target: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

---

## ✅ Completed Tasks

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
