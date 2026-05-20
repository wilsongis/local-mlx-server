---
title: "Run 32B Models on Your Mac With 5x Less Memory: Google’s TurboQuant Hits Apple Silicon"
source: "https://pub.towardsai.net/run-32b-models-on-your-mac-with-5x-less-memory-googles-turboquant-hits-apple-silicon-ad59f9292d1c"
published: 2026-04-15
created: 2026-05-20
description: "Google's TurboQuant lets you run 32B parameter models on Apple Silicon Macs with 5x less memory. Here's how this quantization breakthrough works in practice."
tags:
  - "clippings"
author:
  - "Kashif Mehmood"
---
![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*d09Db33ZvnceIlunXf0IyA.png)

A tweet from Prince Canuma sits at 719,000 views. Posted March 25th: “Just implemented Google’s TurboQuant in MLX and the results are wild!” He attached needle-in-a-haystack benchmarks showing Qwen3.5–35B running at 64K context with 6/6 exact matches at every quantisation level. A 4.9x reduction in KV cache size. On a Mac.

In the ten days that followed, the local LLM community went into a building frenzy. Three separate MLX implementations appeared on GitHub. Someone got Gemma 4 31B running at 128K context with KV memory dropping from 13.3 GB to 4.9 GB. Another developer hit 500ms time-to-first-token on 256K context with a 4B model. A third built custom fused Metal kernels that hit 4.6x compression at 98% of FP16 decode speed.

All of this on consumer Apple Silicon. No cloud. No GPU cluster. Just a Mac.

**The Bottleneck Nobody Talks About**

When you run an LLM locally, memory goes to two places: model weights and the KV cache.

Model weights get all the attention. A 32B parameter model at 4-bit quantisation needs roughly 16–20 GB. You download it from HuggingFace, it sits in memory, and it stays fixed. Most people stop thinking about memory here.

The KV cache is the quiet problem. Every token the model processes adds a key vector and a value vector for every attention layer. In short contexts with small models, this is negligible. At 128K context with a 32B model, your KV cache alone can consume 30–40 GB of memory on top of the model weights. Even an M2 Ultra with 192 GB starts to feel the pressure. For most people running 24–64 GB machines, long-context inference is simply impossible.

Context windows have been growing fast: 32K, 128K, 200K, a million tokens. The models support it. The hardware doesn’t. Not because the chip is too slow, but because the KV cache eats all the memory before the model can finish thinking.

TurboQuant was built to solve exactly this.

**What TurboQuant Actually Is**

TurboQuant is a KV cache compression algorithm from Google Research, published April 2025 (arXiv:2504.19874) and accepted at **\*\*ICLR 2026\*\***. The authors are Amir Zandieh (Research Scientist at Google), Majid Daliri, Majid Hadian, and Vahab Mirrokni (VP and Google Fellow), with collaborators at Google DeepMind, KAIST, and New York University.

The core claim: **4–6x memory reduction with near-zero accuracy loss and no retraining required.** On H100 GPUs, Google reports up to 8x speedup alongside the memory savings.

TurboQuant compresses the KV cache down to 2.5–3.5 bits per element using a two-stage pipeline. The first stage is PolarQuant (separately accepted at AISTATS 2026). The second is QJL, Quantised Johnson-Lindenstrauss. Together, they produce an attention quality that’s nearly indistinguishable from full FP16.

Google also provides a formal proof that TurboQuant operates near the information-theoretic lower bounds on distortion rate for any vector quantizer, differing only by a small constant factor (~2.7x). This isn’t just “it works well empirically.” The math says you can’t do much better than this.

**Stage 1: PolarQuant**

Standard quantisation takes floating-point numbers and maps them to lower-bit representations. The problem: KV cache vectors have outliers. A small number of dimensions carry very large values, and those outliers destroy accuracy when you compress aggressively. Per-channel scaling factors help. They don’t fix it.

PolarQuant starts somewhere unexpected. It applies a random rotation (a Walsh-Hadamard transform) that redistributes outlier values evenly across all dimensions. After rotation, the data becomes approximately Gaussian. No extreme values. Predictable distribution shape. That’s the ideal case for quantisation.

Then it converts the rotated vectors from Cartesian to polar coordinates: direction (a set of angles) and magnitude (a single radius). Direction captures the geometric structure that matters for attention computation. Magnitude is just one scalar per vector. The angles get quantised individually through a recursive polar decomposition (pair coordinates, extract radius and angle, repeat). Each quantised component captures maximum information with minimum bits.

3 bits for direction. 8 bits for magnitude. This preserves key-query relationships far better than naive quantisation because the rotation already eliminates the outliers that would otherwise blow up precision at low bit widths.

And PolarQuant kills the overhead tax. No per-channel scales, no zero-points. Just the codebook and the rotated values. Memory overhead beyond the quantised data itself: effectively zero.

**Stage 2: QJL (Quantised Johnson-Lindenstrauss)**

PolarQuant alone still leaves a small residual error. QJL fixes it with just 1 extra bit per dimension.

Take the difference between the original vector and the PolarQuant reconstruction. Project it through a random matrix (the Johnson-Lindenstrauss transform). Store only the sign bits: +1 or -1 per dimension. During attention computation, an estimator uses these sign projections to calculate the inner product error and correct for it before the softmax.

One bit per dimension. Cheap to store, cheap to compute. But it eliminates the systematic bias that PolarQuant leaves behind. At 2.5–3.5 bits per element total, attention quality matches full FP16 across every benchmark Google tested: LongBench, Needle In A Haystack, ZeroSCROLLS, RULER, and L-Eval on Gemma, Mistral, and Llama-3.1–8B-Instruct.

**The MLX Port**

Google validated TurboQuant on A100 and H100 GPUs running CUDA. Apple Silicon is a completely different beast: unified memory, Metal compute shaders instead of CUDA kernels. The community didn’t wait. Within days, three separate implementations were running on Macs.

**Implementation 1: sharpner/turboquant-mlx**

## [GitHub — sharpner/turboquant-mlx: A proof of concept of googles TurboQuant Paper…](https://github.com/sharpner/turboquant-mlx?source=post_page-----ad59f9292d1c---------------------------------------)

### A proof of concept of googles TurboQuant Paper https://arxiv.org/abs/2504.19874 — sharpner/turboquant-mlx

github.com

The primary implementation offers two distinct compression paths.

**V2 (the speed path)** uses `mx.quantized_matmul`, a Metal-accelerated matrix multiplication built into Apple’s MLX framework. It applies affine quantisation to the KV cache dynamically at inference time. An optional rotation step (random QR decomposition) redistributes outlier values before quantisation. An optional QJL step adds 1-bit residual correction on top. V2 runs at 70–105% of FP16 decode speed depending on variant, with 3.6–4.7x cache compression.

**V3 (the quality path)** implements the paper’s algorithm more faithfully using Lloyd-Max codebook quantisation. Lloyd-Max computes optimal non-uniform quantisation boundaries for Gaussian-distributed data. After the random rotation step, KV cache coordinates are approximately Gaussian, so Lloyd-Max’s 8-level codebook (at 3-bit) places boundaries exactly where the data density is highest. The quality improvement over V2 is real, especially at 3-bit and below. The trade-off: without custom Metal kernels for the codebook lookup, V3 runs 5–6x slower than V2.

**Implementation 2: flovflo/turboquant-mlx-qwen35-kv**

## [GitHub — Flovflo/turboquant-mlx-qwen35-kv: Experimental TurboQuant-inspired KV-cache backend for…](https://github.com/flovflo/turboquant-mlx-qwen35-kv?source=post_page-----ad59f9292d1c---------------------------------------)

### Experimental TurboQuant-inspired KV-cache backend for MLX Qwen3.5 with baseline and MLX KV quantization benchmarks …

github.com

Targets Qwen3 and Qwen3.5 specifically. Demonstrated on `mlx-community/Qwen3.5–35B-A3B-4bit` with a 26% reduction in generation wall time, 679 tokens/sec prompt throughput, and 44.8 tokens/sec generation.

**Implementation 3: arozanov/turboquant-mlx**

## [GitHub — arozanov/turboquant-mlx: TurboQuant KV cache compression for MLX with fused Metal kernels…](https://github.com/arozanov/turboquant-mlx?source=post_page-----ad59f9292d1c---------------------------------------)

### TurboQuant KV cache compression for MLX with fused Metal kernels. 4.6x compression at 98% FP16 speed. …

github.com

Built custom fused Metal kernels from scratch to solve V3’s speed problem. The development arc tells the story of optimisation on Apple Silicon: the initial Python-only implementation ran at 0.28x FP16 speed. After successive rounds of Metal kernel optimisation (fusing the quantisation, dequantization, and matrix multiplication into single GPU dispatches), it reached **0.91–0.98x FP16 speed at 4.6x compression**. Tested on Qwen2.5–32B-Instruct-4bit running on an M4 Pro with 48 GB, at 16K context, KV memory dropped from 4.2 GB to 897 MB with identical quality to FP16 baseline.

This is the implementation that works as a drop-in replacement for mlx-lm’s KVCache.

**The Benchmark Numbers**

Tested on Apple M4 Max with 64 GB unified memory, using 4-bit weight-quantised models from mlx-community. KV cache at 8192 tokens.

**Compression Ratios**

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*GvaiUCZ0dPKz1_Xb51gC9g.png)

**Quality Impact (Perplexity, Lower Is Better)**

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*B1nAxY9WUB1n2x56GrfVkg.png)

Two results stand out. V2 4-bit rotated actually **beats** FP16 on Llama 3.2 3B by 0.8%, because the rotation acts as a regularizer. V2 3-bit rot+QJL beats FP16 on Gemma 3 4B by 1.1%. This isn’t measurement noise. Gemma has D=256 head dimensions compared to D=128 on Llama, and larger head dimensions compress much more effectively. If you’re running Gemma models, you’ll get better results than Llama at the same bit width.

**Decode Speed (Llama 3.2 3B, tokens/sec)**

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*54VLXnjRk54PXl0Gkc2SNQ.png)

V2 4-bit LEAN actually runs faster than FP16 at long contexts (156 vs 148 tok/s at T=8192) because the compressed cache fits better in the memory hierarchy. V3 paths are significantly slower without custom Metal kernels, which is why Arozanov’s fused kernel implementation matters.

**What People Are Building With It**

Benchmarks are synthetic. Here’s what people are actually doing with it.

**Prince Canuma** ran needle-in-a-haystack tests on Qwen3.5–35B-A3B across 8.5K, 32.7K, and 64.2K context lengths. 6/6 exact matches at every quantisation level. TurboQuant 2.5-bit gave him 4.9x smaller KV cache. 3.5-bit gave 3.8x. His follow-up the next day: “TurboQuant MLX kernels are closing the gap on decode speed, now within 15–30% of full precision.”

His most dramatic result came with Gemma 4 31B at 128K context. KV memory dropped from 13.3 GB to 4.9 GB (63% reduction). Peak memory fell from 75.2 GB to 65.8 GB. “TurboQuant compression scales with sequence length,” he noted. “So the longer the context, the bigger the savings.” That scaling property matters because it means the benefit grows exactly where you need it most.

**John T Davies** pushed the practical angle further. He pre-filled a 256K KV cache with documents and system prompts using Qwen3.5–4B, quantised it with TurboQuant, and ran queries against it. For a 75-page PDF (roughly 30K tokens), he measured sub-150ms time-to-first-token. He runs this setup on a Mac Mini in his office as a server for staff to query confidential company documents from phones, iPads, and laptops. No cloud, no API costs, no data leaving the building.

He also demonstrated it on 17K lines of code from 177 source files, plus an index of the entire 1,902-file Claude Code codebase. His description: “MLX + TurboQuant = Local Super Power.”

**From r/LocalLLaMA**, one developer reported “4.6x KV cache compression at 0.98x FP16 speed on Qwen2.5–32B” using custom Metal kernels. Another cut to the practical point: “If you can run 27B on 24GB, TurboQuant gets you like 3–4x more context for the same memory budget.”

**Alican Kiraz** released a v0.1 research preview (Qwen3.5-TurboQuant-MLX-LM) running TurboQuant on Qwen3 and Qwen3.5 full-attention KV cache layers. **SharpAI** shipped SwiftLM, a native MLX Swift inference server with OpenAI-compatible API, SSD streaming for 100B+ MoE models, and TurboQuant KV cache compression baked in, plus an iOS app.

Not everything is smooth. Some llama.cpp tests on Apple Silicon/Metal showed KV usage “kept in check” for long contexts, but token generation dropped 50% vs FP16. Early CUDA ports produced unusable outputs before being fixed. V3 without custom Metal kernels runs 5–6x slower than V2, making it impractical for interactive use until Arozanov’s fused kernel work. Community consensus: a real upgrade for consumer Macs, but V3 speed and edge-case quality regressions at 2.5-bit on D=128 models need more work before anyone should trust it blindly in production.

**How to Start Using It**

Requirements: Apple Silicon Mac, Python 3.10+.

```c
pip install mlx mlx-lm
git clone https://github.com/sharpner/turboquant-mlx
cd turboquant-mlx
python run_llm.py
```

To use TurboQuant compression in your own code, monkey-patch the SDPA dispatch and pass a custom cache object:

```c
import mlx_lm
from turboquant.cache_v2 import TurboQuantKVCacheV2
import turboquant.patch as tq_patch
tq_patch.apply() # Monkey-patch SDPA dispatch
model, tokenizer = mlx_lm.load("mlx-community/Llama-3.2–3B-Instruct-4bit")
head_dim = model.layers[0].self_attn.head_dim
n_layers = len(model.layers)
# V2 4-bit rotated: fastest near-lossless option
cache = [
TurboQuantKVCacheV2(
head_dim=head_dim,
bits=4,
group_size=64,
use_rotation=True,
use_normalization=True,
)
for _ in range(n_layers)
]
```

**Choosing Your Strategy**

**Maximum speed:** V2 4-bit LEAN. Runs at ~105% of FP16 decode speed at T=8K, 3.6x compression. Best for interactive chat where response time is everything.

**Best quality at 4-bit:** V2 4-bit rotated. Slight quality improvement over FP16 baseline (-0.8% perplexity on Llama), 3.6x compression. The sweet spot for most use cases.

**Best 3-bit on large heads:** V2 3-bit rot+QJL. Actually beats FP16 on Gemma models (D=256). If you’re running Gemma 3 4B or Gemma 4, start here.

**Near-lossless max compression:** V3 3.5-bit mixed. 4.1x compression with only +0.3% perplexity on Llama. Use when you need significantly more context headroom with minimal quality impact. Requires tolerance for slower decode until Metal kernel support catches up.

**Aggressive compression:** V3 2.5-bit mixed. 5.5x compression. Works well on D=256 models (+7% perplexity on Gemma) but hits harder on D=128 models (+27% on Llama). Acceptable for long-context batch processing, not recommended for interactive chat.

For the drop-in replacement approach (no monkey-patching), use arozanov/turboquant-mlx with its fused Metal kernels and mlx-lm KVCache compatibility.

**Why This Matters Right Now**

Models aren’t getting smaller. Gemma 4 31B, Qwen3.5–35B, Llama 4. The KV cache problem scales with both model size and context length, and both numbers keep going up.

Context windows have already blown past what consumer hardware can handle at full precision. Claude does 200K tokens. Gemini goes to a million. People want the same from local models: code review across an entire repo, long document Q&A, and agent workflows with extended conversation histories. Without KV cache compression, those workloads stay locked behind cloud APIs.

TurboQuant won’t make your Mac match a cloud GPU cluster. But it removes the specific bottleneck blocking the most useful local use cases: fitting enough context into memory to do real work. 8K context on a 32B model is a toy demo. 32K context is a useful tool. That’s what 3.6x compression buys you.

The MLX ecosystem isn’t waiting around either. The mlx-vlm library hit v0.4.3 with day-zero Gemma 4 support and TurboQuant integration. An active PR sits in the core mlx-lm library. SharpAI’s SwiftLM brings TurboQuant to a native Swift server with an iOS app. Ten days. One proof-of-concept repo to multiple production-quality implementations.

**Paper:** [arXiv:2504.19874](https://arxiv.org/abs/2504.19874) (ICLR 2026) | **Google Blog:** [TurboQuant: Redefining AI Efficiency](https://research.google/blog/turboquant-redefining-ai-efficiency-with-extreme-compression/) | **Code (sharpner):** [github.com/sharpner/turboquant-mlx](https://github.com/sharpner/turboquant-mlx) | **Code (arozanov):** [github.com/arozanov/turboquant-mlx](https://github.com/arozanov/turboquant-mlx) | **Code (flovflo):** [github.com/flovflo/turboquant-mlx-qwen35-kv](https://github.com/flovflo/turboquant-mlx-qwen35-kv) | **SwiftLM:** [github.com/SharpAI/SwiftLM](https://github.com/SharpAI/SwiftLM)

## [TurboQuant: Online Vector Quantization with Near-optimal Distortion Rate](https://arxiv.org/abs/2504.19874?source=post_page-----ad59f9292d1c---------------------------------------)

### Vector quantization, a problem rooted in Shannon’s source coding theory, aims to quantize high-dimensional Euclidean…

arxiv.org

## [TurboQuant: Redefining AI efficiency with extreme compression](https://research.google/blog/turboquant-redefining-ai-efficiency-with-extreme-compression/?source=post_page-----ad59f9292d1c---------------------------------------)

### Vectors are the fundamental way AI models understand and process information. Small vectors describe simple attributes…

research.google

## [GitHub — SharpAI/SwiftLM: ⚡ Native MLX Swift LLM inference server for Apple Silicon…](https://github.com/SharpAI/SwiftLM?source=post_page-----ad59f9292d1c---------------------------------------)

### ⚡ Native MLX Swift LLM inference server for Apple Silicon. OpenAI-compatible API, SSD streaming for 100B+ MoE models…

github.com