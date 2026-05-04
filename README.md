# Local MLX Server

## Quick Navigation by Persona

### 🖥️ Operators (Run the Server)
- [Operations Guide](OPERATIONS.md) - Server startup, `just` recipes, monitoring, and troubleshooting

### 👩‍💻 Contributors (Add Code/Docs)
- [Contributing Guide](CONTRIBUTING.md) - Setup, development workflow, testing, and PR process
- [Agent Rules](AGENTS.md) - Operational charter, `/speckit.*` commands, and agent guidelines

### 🛡️ Maintainers (Governance)
- [Governance](GOVERNANCE.md) - Constitution, documentation standards, release processes, and project policies

## Project Overview

Local MLX Server is an isolated inference infrastructure repository for running very large Mixture-of-Experts LLMs locally on Apple Silicon, with a practical focus on 120B+ class models such as GPT-OSS and Nemotron variants.

The project exists to solve one bottleneck: memory pressure from both model weights and runtime KV cache when context length grows.

## The Core Problem

Running 120B+ MoE models locally is usually blocked by unified memory limits, even when only a subset of experts is active per token.

- MoE models still require all expert weights resident in memory.
- Standard formats can fail to fit practical hardware tiers.
- KV cache scales with context length and can consume multiple additional GB at long prompts.
- This is especially critical on Apple Silicon machines in the 64 GB and 96 GB unified memory tiers, where memory headroom directly determines whether long-context inference is possible.

## Technical Solution: TurboQuant Methodology Adapted to MLX

This repository centers on the TurboQuant-MLX approach described in the research notes under `docs/research`.

### 1) Weight Compression for MoE

- Use Hadamard-based rotation to Gaussianize weight distributions.
- Apply Lloyd-Max style codebook quantization to match Gaussian-like post-rotation distributions.
- Extend quantization to MoE expert-heavy architectures, including packed expert representations and efficient MoE kernel paths.

### 2) Per-Path Hybrid Quantization

A key capability is per-path bit allocation instead of one uniform bit-width:

- Attention path kept at higher precision (example: 3-bit attention).
- Expert path compressed more aggressively (example: 2-bit experts).
- Grouped quantization settings (example: group size 32) used to hit memory targets.

Why this matters:

- Attention is more error-sensitive during autoregressive decoding.
- Expert parameters dominate total size, so lowering expert bit-width drives major memory reduction.
- This hybrid split enabled practical 120B deployment on tighter memory budgets in the referenced experiments.

### 3) KV Cache Compression

TurboQuant is also applied to KV cache storage:

- On-the-fly KV compression using rotation + codebook quantization.
- Approximately 4x to 4.6x KV cache compression in reported configurations.
- Materially lowers runtime memory at long context lengths.
- For very large models, reduced memory traffic can also improve throughput.

## What This Repository Is Building Toward

The infrastructure goal is explicit:

- A standalone, lightweight inference hub.
- Dependency and environment management through `uv`.
- A localized OpenAI-compatible API endpoint powered by `mlx_lm.server`.
- Reliable local serving for agentic coding tools and adjacent local automation systems.

This repository is not intended to become an application monolith. It is the model-serving backbone.

## Scope and Non-Goals

**In scope**:

- Reproducible local server startup and operational scripts.
- MLX and TurboQuant integration updates.
- Inference argument tuning for memory, latency, and quality tradeoffs.
- Stable OpenAI-compatible local API behavior.

**Out of scope**:

- Building full-stack web products in this directory.
- App UI frameworks and product-level backend features.
- Data platform expansion unrelated to inference serving.

## Related Documentation

- [Operations Guide](OPERATIONS.md) - Detailed operational procedures and `just` command reference
- [Agent Rules](AGENTS.md) - Operational charter for AI agents working in this repository
- [Governance](GOVERNANCE.md) - Project constitution, standards, and governance policies
- [Contributing](CONTRIBUTING.md) - Guidelines for contributors
