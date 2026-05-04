---
title: "Nemotron 120B on a 48 GB MacBook: 27 tok/s with TurboQuant Hybrid Quantization (MLX)"
source: "https://medium.com/@manjunath.shiva/nemotron-120b-on-a-48-gb-macbook-27-tok-s-with-turboquant-hybrid-quantization-mlx-529d93cbc960"
published: 2026-04-30
created: 2026-05-04
description: "More"
tags:
  - "clippings"
author:
  - "Manjunath Janardhan"
---
*Per-path hybrid 3-bit/2-bit quantization fits a 120B Mamba + MoE model in 36 GB on disk and 40.8 GB peak — runs on Apple Silicon with no sysctl tweaks, no calibration data*

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*7tBn8Lb0xGZrDEzLTr9IUA.jpeg)

Image by Manjunath Janardhan. Generated using Google Nano Banana 2

NVIDIA’s **Nemotron-3-Super-120B-A12B** is a 120B-parameter hybrid Mamba + MoE + sparse-attention model with 512 routed experts and a latent-MoE design. This article is the first publicly available quantization that runs it on a **48 GB Apple Silicon MacBook** — at **27.2 tokens/sec**, using **TurboQuant-MLX** with a new per-path hybrid bit-allocation scheme (3-bit attention, 2-bit experts, group size 32). The compressed model is ~36 GB on disk, with a peak unified memory of 40.8 GB, and requires no calibration data.

This is Part 4 of a series on TurboQuant for Apple Silicon. In Part 1of the series, I adapted Google’s TurboQuant for dense-model weight compression on MLX (1B-7B). In Part 2, I extended it to Mixture-of-Experts and got GPT-OSS-120B running at 44 tok/s on a 64 GB Mac, then Qwen3.5–122B at 26.5 tok/s. In Part 3, I added KV cache compression — 4.6× smaller, *faster* on 120B+ models. Every result so far had the same fine print: **64 GB Mac required**.

If you have not read or want to read Part 1, Part 2 and/or Part 3, here are the links

Part 1:

## [I Built a Quantization Method That Beats Standard 4-bit on a 7B Model — With Zero Training Data](https://ai.gopubby.com/i-built-a-quantization-method-that-beats-standard-4-bit-on-a-7b-model-with-zero-training-data-fe37c2fb4952?source=post_page-----529d93cbc960---------------------------------------)

### Adapting Google’s TurboQuant for weight compression on Apple Silicon using MLX, and what the perplexity numbers…

ai.gopubby.com

Part 2:

## [How I run 122B-parameter LLMs on a MacBook — outperforming MXFP4 and standard quantization on…](https://medium.com/data-science-collective/how-i-run-122b-parameter-llms-on-a-macbook-outperforming-mxfp4-and-standard-quantization-on-apple-0552ee3da1f7?source=post_page-----529d93cbc960---------------------------------------)

### I extended TurboQuant to Mixture-of-Experts models. A 120B LLM that no existing format could fit on 64GB now runs at 44…

medium.com

Part 3:

## [TurboQuant: Compressing KV cache 4x on Apple Silicon — how I doubled the usable context length.](https://medium.com/data-science-collective/turboquant-compressing-kv-cache-4x-on-apple-silicon-how-i-doubled-the-usable-context-length-5a8bce975fe2?source=post_page-----529d93cbc960---------------------------------------)

medium.com

The 64 GB tier is not the entry point for Apple Silicon. The 48 GB MacBook Pro 14" is. And the 36 GB / 32 GB tiers are everywhere. So when NVIDIA released Nemotron-3-Super-120B-A12B, the question that mattered was: *can we get this onto a 48 GB Mac?*

The honest first answer was no. A uniform 3-bit TurboQuant at group size 32 produced a ~50 GB on-disk model whose first decode call promptly triggered a Metal \`Insufficient Memory\` failure on a stock 64 GB machine, because peak memory exceeded the default \`iogpu.wired\_limit\_mb=49152\` cap. You can raise that cap with a \`sysctl\` knob, but that’s a 64 GB-machine workaround, not a 48 GB-machine answer.

This article is about the answer: a per-path hybrid quantization (3-bit attention, 2-bit experts, group size 32) that drops the model to **~36 GB on disk and 40.8 GB peak unified memory**, decodes at **27.2 tokens/sec** on M-series silicon (measured: 779-token generation), fits the default wired-memory cap with headroom, and ships today on PyPI and HuggingFace. There’s also one Phase-1 caveat about step-by-step arithmetic that I’ll cover — it’s the Phase-2 problem.

**Want to try it as you read?** On any Apple Silicon Mac with Xcode Command Line Tools and CMake 3.27+ installed:

```c
pip install "turboquant-mlx-full>=0.1.6"

hf download manjunathshiva/Nemotron-3-Super-120B-A12B-tq3a-tq2e-g32 - local-dir ~/models/nemotron-120b-48gb
```

A complete copy-pasteable usage recipe is at the end of the article in the Try it yourself section.

## Why 48 GB matters more than 64 GB

The chart of who actually owns Apple Silicon machines is heavily weighted toward 16/24/32 GB; the 48 GB tier is the smallest configuration that has *any* realistic shot at running a 120B model.

The default OS-level cap on how much unified memory the GPU can wire on a 64 GB Mac is \`iogpu.wired\_limit\_mb=49152\` — 48 GB. The 48 GB MacBook hits the same cap from the other direction: it physically has 48 GB total. So a model that “fits 64 GB at default settings” and a model that “fits 48 GB at all” are the *same constraint*: peak unified memory ≤ 48 GB.

That number — 48 GB peak — became the design target.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*4EEUEvX0fghTxNjPF7PWEw.jpeg)

Image by Manjunath Janardhan.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*v4V8MK72g7q4mplG5-NSSA.png)

Apple Silicon RAM tier vs largest TurboQuant-runnable model. The 48 GB bar finally has a 120B-class entry.

The 64 GB tier already had GPT-OSS-120B (Part 2) and Qwen3.5–122B (Part 2 update). The 48 GB tier had nothing in the 100B+ class. Part 4 fills that gap.

### What’s different about Nemotron-3-Super-120B-A12B

Nemotron-3 isn’t a “Transformer with experts.” It’s a *hybrid* model with three different layer types interleaved, plus a multi-token-prediction head, plus a latent-MoE design that I hadn’t seen anywhere else. Walking through the architecture is worth a section because every choice TurboQuant has to make depends on it.

**The layer pattern.** Nemotron-3 Super has 88 layers in a recurring override sequence:

```c
M E M E M E M * E M E M E M E M * …
```

where \`M\` is a Mamba state-space layer (cheap for long context), \`E\` is an MoE layer, and \`\*\` is a sparse-attention layer used only where it earns its keep. There are **no dense MLP layers anywhere** — every FFN computation flows through the MoE, and every long-range mixing decision is split between Mamba and the rare attention layer.

**The expert pool.** Each MoE layer has **512 routed experts plus 1 shared expert**. That’s 4× more experts than GPT-OSS-120B (128) and 2× more than Qwen3.5–122B (256). With 12B active parameters per token, the router is doing real work.

**The latent-MoE trick.** This is the part that makes Nemotron-3 fundamentally different. Instead of giving each of the 512 experts its own full weight matrices, every expert shares a single 1024-dimensional **latent projection space** (\`fc1\_latent\_proj\`, \`fc2\_latent\_proj\`). Each expert is, in effect, a small specialization on top of a shared pantry. From a quantization perspective, this is enormous: **quantizing the shared latent space compresses every one of the 512 experts at once**. The cost-per-bit-saved is staggering.

**The bonus head.** There’s a multi-token-prediction (MTP) head bolted on the end. It has its own linears that need quantizing.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*myfsl97ljUMwvGx7kDCXBA.jpeg)

Image by Manjunath Janardhan.

That last column is where the trap lives. BF16 Nemotron-3 is 240 GB. To fit a 48 GB Mac at the default wired-memory cap, the compressed model has to be **6× smaller than BF16** *and* **hold peak memory under 40 GB at decode**. Uniform 3-bit at group size 32 (~50 GB on disk, ~55 GB peak) misses both numbers. We need to be smarter about where the bits go.

### The wall: uniform 3-bit doesn’t fit 48 GB

The version of this section: I tried the obvious thing first, and it didn’t work.

I converted Nemotron-3 with TurboQuant uniform 3-bit at group size 32, expecting it to be done. The on-disk model was about 50 GB. Loading worked. Then the first generation step crashed:

```c
[METAL] Command buffer execution failed: Insufficient Memory
```

Tracing peak memory with \`mx.metal.get\_active\_memory()\` showed the model peaking at ~55 GB during decode — comfortably above the default \`iogpu.wired\_limit\_mb=49152\` cap. On a 64 GB machine you can raise the cap with \`sudo sysctl iogpu.wired\_limit\_mb=61440\` and the model runs. But:

1\. That doesn’t help a 48 GB MacBook, which physically can’t go higher.

2\. Raising the wired cap means *every other process on the machine* loses memory. It’s not the right user experience.

3\. ~50 GB on disk is also a slow download for someone trying out the model.

The fix had to come from quantization, not from system tuning.

### The idea: per-path hybrid bit allocation

When a uniform bit-width misses the budget, the natural next move is non-uniform: spend more bits where they matter, fewer bits where they don’t. The question is *where*.

The first two articles have already been answered in the negative form. Part 2 documented a “2-bit generation cliff” on GPT-OSS — perplexity numbers looked fine, but autoregressive output collapsed within 20 tokens. The forensics pointed at **attention**: small errors in the QK^T logits compound through softmax, and once the attention pattern drifts the model can’t recover. The expert weights, by contrast, are read sparsely (k-of-N routing), and noise in any individual expert is averaged across many tokens. **Attention is precision-critical; experts are precision-tolerant.**

Now look at where the parameters actually live in Nemotron-3:

\- Attention path (Q/K/V/O across all \`\*\` layers): **small**.

\- Expert path (routed experts + latent-MoE projections + shared expert + MTP head): **~90% of parameters**.

That’s a per-path optimization waiting to happen. So I added a \`bits\_for\_path(layer\_idx, param\_path) → bits\` hook into the conversion pipeline. The default policy that ships in v0.1.6:

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*keSJEnMofBUvqdcmVwllyg.jpeg)

Image By Manjunath Janardhan.

I call this configuration **tq3a-tq2e g32** (3-bit attention, 2-bit experts, group size 32). The naming is intentional — once per-path bit allocation exists, you can imagine other splits (tq4a-tq2e for an “even safer” attention path, tq3a-tq3e g64 for a “uniform fallback” baseline, etc.).

The economics work out beautifully on Nemotron-3 specifically because of latent-MoE. Quantizing \`fc1\_latent\_proj\` and \`fc2\_latent\_proj\` at 2-bit applies *\*once per layer\** and compresses all 512 experts in that layer simultaneously. There’s no per-expert cost to chase.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*kf5b39g4ZZCKlO4IaIqbHw.jpeg)

Per-path bit allocation for Nemotron-3 Super. The shared latent-MoE projection (yellow) takes the 2-bit hit and compresses all 512 experts at once; the small attention pantry (blue) stays at 3-bit where precision matters most. Source: Manjunath Janardhan experiments.

### The result: 36 GB on disk, 40.8 GB peak, 27.2 tok/s

The numbers, on an M-series MacBook with macOS, MLX, and \`turboquant-mlx-full\` 0.1.6 (779-token generation, sampler-B config: \`temp=0.7 rep\_penalty=1.04 rep\_ctx=256\`):

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*0fkEv3OWrXIVGSvtpodtkg.jpeg)

Image By Manjunath Janardhan. Comparsion of Model Configuration and Performace.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*WJzaNXh9wkA4gi8STQzpxg.png)

BF16 vs uniform 3-bit vs hybrid tq3a-tq2e on Nemotron-3 Super 120B.The hybrid is the first row that fits both the on-disk and peak-memory. budgets for a 48 GB Mac. Source: Manjunath Janardhan experiments.

Three things to call out from that table:

1\. **The disk-size delta is 28%.** Uniform 3-bit g32 → hybrid tq3a-tq2e g32 saves ~14 GB of model weights. That savings is almost entirely the experts — the attention pantry stays at 3-bit and barely changes.

2\. **Peak memory drops by ~14 GB.** ~55 GB → 40.8 GB. This isn’t just the disk-size delta — it’s also that 2-bit packed weights stream off disk faster, the dequant intermediate buffers are smaller, and the routing tensors that fan out across experts shrink. The full memory pipeline gets healthier.

3\. **Decode speed** *increases* from ~19 tok/s to **27.2 tok/s** (measured on a 779-token generation). This is the same effect Part 3 documented for KV cache compression on GPT-OSS-120B: when a model is memory-bandwidth-bound (and a 120B at 88 layers absolutely is), a smaller representation reads faster. 2-bit experts are 33% less data per layer for the dominant compute path. That bandwidth saving outweighs the slightly more complex codebook lookup.

The last one is what makes this not just a “fits 48 GB” story but a “ *better* on 48 GB” story. The smaller hybrid runs faster than the larger uniform 3-bit it’s replacing.

### Long-context decode: the kernel fix

A quieter but equally important bit of work was making sure the model actually works in a long context. On the first attempts, prompts past a few thousand tokens crashed the fused gather kernel with an argument-validation error. The trace pointed to \`polar\_multi\_gather\_qmv\` — the kernel from Part 2 that handles per-expert input vectors for the MoE down-projection.

The diagnosis: in the long context, the per-token expert routing produces argument tensors whose total flat size exceeds the Metal indirect-buffer threshold. The kernel itself was fine — the launch wrapper was passing too much routing metadata in a single dispatch.

The fix is a chunked-launch wrapper that splits routing into batches of \`K\_CHUNK=4096\` tokens and transparently dispatches multiple kernel invocations when the prompt is long. From the caller’s perspective, nothing changes — same function signature, same return shape — but internally a 12,000-token prompt is now three back-to-back kernel launches instead of one over-budget one.

With this fix, the now-classic “needle in a haystack” prompt works:

**Prompt:** 2000 words of filler about photography → “the password is **\*\*avocado-37-volcano\*\*** ” → 2000 words of filler about cooking → “What was the password?”

The model recovers \`avocado-37-volcano\` reliably, including in its \`<think>\` reasoning trace, on a 4000+-token context. Same recipe, no special configuration:

```c
python -m turboquant_mlx.generate \
 - model ~/models/nemotron-120b-48gb \
 - prompt "$(cat tests/needle_4k.txt)" \
 - max-tokens 512 - min-tokens 50 \
 - temp 0.7 - rep-penalty 1.04 - rep-ctx 256
```

## Stress-test results: 5 of 6 pass cleanly

I ran a 6-test stress harness against the hybrid model with the recommended decode config (\`temp=0.7\`, \`rep\_penalty=1.04\`, \`rep\_ctx=256\`). The harness tries to break the model in different ways: long-form prose, arithmetic, code, long-context retrieval, strict formatting, and an open-ended, very-long-output prompt that historically triggers degenerate-tail loops.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*ByppmmbGX2z-oM86nbejmg.jpeg)

Image by Manjunath Janardhan. Stress test Results

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*QyhilNcMGcxBqR3cpBtMTw.png)

6-test stress harness on Nemotron-3 Super tq3a-tq2e g32. Five of six tests pass cleanly; only step-by-step arithmetic shows the Phase-1 limitation. Source: Manjunath Janardhan experiments.

5 out of 6 — including the historically long-essay and very-long-output cases that earlier sampler configurations crashed and burned on. The numbered-list and code tests in particular are interesting: both require *\*exiting\** the \`<think>\` reasoning trace at the right moment and returning to clean, formatted output, and both pass without coaxing.

### The one caveat: math accuracy in Phase 1

Test 2 above is the honest part. On step-by-step numeric reasoning (“a train leaves Boston at 9 AM going 60 mph…”) the hybrid produces a complete, well-structured chain of reasoning at the right level of detail — and then lands the wrong number at the end.

The diagnosis took a while. Sampler tuning isn’t the lever — I swept three configurations across \`rep\_penalty ∈ {1.03, 1.04, 1.05, 1.15}\` and \`temp ∈ {0.5, 0.7, 0.8}\` and the math regression is consistent. The tightest pattern: **any non-zero \`rep\_penalty\` causes small slips in arithmetic during long reasoning chains**. The slips originate in the 2-bit expert path — when the model is doing many almost-identical token-by-token computations (carrying digits, threading the same equation forward), small per-token codebook errors land near the same 2-bit quantization boundary repeatedly, and the repetition penalty subtly biases away from the *\*correct\** repeated token because the previous, also-correct token is already in the rep-penalty window.

The workaround that ships in Phase 1 is a per-prompt instruction: **for math/numeric prompts, omit \` — rep-penalty\`**.

```c
# For a numeric prompt - drop the repetition penalty entirely
python -m turboquant_mlx.generate \
 - model ~/models/nemotron-120b-48gb \
 - prompt "A train leaves Boston at 9:00 AM going 60 mph…" \
 - max-tokens 2048 - min-tokens 50 \
 - temp 0.7
```

**The cost:** without \`rep\_penalty\` you may see degenerate-tail loops (em-dash runs, repeated bracket sequences) on long open-ended outputs. So the Phase-1 rule is: use \`rep\_penalty=1.04 rep\_ctx=256\` as the default, drop it when the prompt is dominantly numeric, and reach for the standard uniform 3-bit Nemotron variant if you have a 64 GB machine and need rock-solid arithmetic.

This is a **Phase-1 ceiling, not a permanent one**. The next section is what I’m doing about it.

### Phase 2: a calibration-data Lloyd-Max codebook

Three candidate fixes are on the bench for Phase 2:

1\. **First/last-layer bit protection.** Keep layers 0, 1, 86, 87 at 3-bit even on the expert path. Architectural prior; cheap to try; won’t change disk size much because those layers are a small fraction.

2\. **Calibration-data Lloyd-Max codebook.** Replace the data-free Lloyd-Max codebook (computed once from \`N(0,1)\` and embedded as a constant) with a codebook trained on a small post-rotation activation sample from the model itself. Algorithmic; preserves the 36 GB disk size and 27.2 tok/s decode speed; targets the actual error distribution the experts produce.

3\. **Fused QJL Metal kernel for \`PolarQuantizedSwitchLinear\`.** The 1-bit residual correction from Part 1 is already implemented for dense linears. Wiring it into the SwitchLinear path requires a fused Metal kernel that doesn’t yet exist; my earlier attempt at the unfused path was unusable (28 minutes for a single stress test that the hybrid finishes in 2). Kernel-level work; likely fixes math entirely; adds ~1 bit of effective storage.

The current plan is **option 2 first**. The reasoning:

\- It keeps every existing user-facing number constant: 36 GB on disk, 40.8 GB peak memory, 27.2 tok/s decode. The codebook is *the same shape and same size*; only the values inside it change.

\- It targets the failure mode directly. The hypothesis is that the data-free \`N(0,1)\` codebook is suboptimal for the long-tailed expert activation distribution that emerges after Hadamard rotation; a codebook trained on real activations should land its centroids closer to where the density actually lives.

\- It’s the single cleanest Phase-2 step. If it works, the math caveat goes away with no API changes and no model-size regression.

The work splits into roughly: a \` — calibration-source\` flag in \`convert.py\`, a new \`core/calibrated\_codebook.py\` module that runs k-means / Lloyd iterations on real activation samples, optional per-layer codebook support if the trained codebooks differ enough across layers to warrant it, one re-conversion (~30 min), one stress run (~12 min). A few hours of code, on the order of a day of measurement.

If option 2 doesn’t fully close the gap, options 1 and 3 are still on the table.

## Try it yourself

Everything in this article ships as one PyPI package and one HuggingFace repo.

```c
# 1. Install (takes about a minute; builds a small Metal extension on install)
pip install "turboquant-mlx-full>=0.1.6" "mlx-lm>=0.31.3"
# 2. Download the pre-converted hybrid model (~36 GB on disk)
hf download manjunathshiva/Nemotron-3-Super-120B-A12B-tq3a-tq2e-g32 \
 -local-dir ~/models/nemotron-120b-48gb
# 3. Generate (recommended config for prose / code / format / long-context)
python -m turboquant_mlx.generate \
 -model ~/models/nemotron-120b-48gb \
 -prompt "Why is the sky blue? Explain in detail." \
 -max-tokens 4096 - min-tokens 50 \
 -temp 0.7 - rep-penalty 1.04 - rep-ctx 256
```

The \` — min-tokens 50\` flag is required for Nemotron-3 Super specifically — the model emits a \`<think>\` reasoning trace before its final answer, and the chat template primes EOS as the top-1 logit at the start of the assistant turn, so without a minimum-token floor the model would terminate before it has actually said anything.

For a numeric prompt, drop the repetition penalty (per the Phase-1 caveat above):

```c
python -m turboquant_mlx.generate \
 -model ~/models/nemotron-120b-48gb \
 -prompt "A train leaves Boston at 9:00 AM going 60 mph…" \
 -max-tokens 2048 - min-tokens 50 \
 -temp 0.7
```

From Python, the same recipe via \`mlx-lm\`:

```c
from mlx_lm import load, generate
from mlx_lm.sample_utils import make_sampler, make_logits_processors

model, tokenizer = load("manjunathshiva/Nemotron-3-Super-120B-A12B-tq3a-tq2e-g32")

sampler = make_sampler(temp=0.7)

processors = make_logits_processors(repetition_penalty=1.04, repetition_context_size=256)

response = generate(

  model, tokenizer,

  prompt="Why is the sky blue? Explain in simple terms.",

  max_tokens=200,

  sampler=sampler,

  logits_processors=processors,
)

print(response)
```

If you want to convert the model yourself (instead of downloading the pre-converted weights), the per-path policy is exposed as flags on the conversion CLI:

```c
turboquant-convert \
 -hf-path nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16 \
 -bits 2 - attn-bits 3 - mlp-bits 2 - group-size 32 \
 -mlx-path nemotron-120b-48gb-mine
```

\` — bits\` sets the default; \` — attn-bits\` and \` — mlp-bits\` override the default on the attention and MoE paths respectively. The conversion takes ~30 minutes on an M-series Mac and runs without any calibration data — it’s the same data-free Hadamard + Lloyd-Max recipe from Parts 1–3, just with a per-path bit-width hook.

If you discover something interesting (or break something) on a configuration I haven’t tested, please file an issue or PR on the Github repo https://github.com/manjunathshiva/turboquant-mlx — the 48 GB tier is wide open and the per-path policy is a knob that hasn’t been swept yet.

## What I learned

**The 48 GB tier was sitting right there.** Every previous result in this series targeted 64 GB because that was the easy number to hit. Designing for 40 GB peak instead of 50 GB peak was uncomfortable for one afternoon and then turned into the most-used variant. There is real value in fitting the next-smaller tier even when the previous tier already worked.

**Per-path bit allocation generalizes.** I built the \`bits\_for\_path()\` hook for one specific Nemotron problem, but it’s now a knob on the conversion CLI that any architecture can use. The natural follow-up is to *\*search\** the bit-width policy automatically over a calibration loss instead of hand-coding it — that’s a Phase 3 idea.

**Latent-MoE is a quantization gift.** Quantizing 512 experts the usual way would have been brutal. Quantizing one shared 1024-dimensional projection that 512 experts route through is trivial. Architecture choices that look like efficiency wins for inference often turn out to be efficiency wins for compression too.

**Sampler tuning is not a substitute for fixing the codebook.** I spent more time than I’d like to admit sweeping \`rep\_penalty\` × \`rep\_ctx\` × \`temp\` looking for a config that fixed math. The best sampler config (\`1.04 / 256 / 0.7\`) is still the right default — but it doesn’t fix arithmetic, because arithmetic isn’t a sampling problem. It’s a quantization-error-distribution problem, and the right fix lives at the codebook layer, not the sampler layer.

**Math accuracy is a great Phase-2 target.** Calling out a known limitation in the model card and naming the specific Phase-2 work to address it has been more useful than burying it. The Phase-1 model is already useful for prose/code/format/long-context on 48 GB Macs; Phase 2 will widen the use cases without changing any of the user-facing constraints.

## Resources

\-TurboQuant paper: [https://arxiv.org/abs/2504.19874](https://arxiv.org/abs/2504.19874) — Zandieh, Han, Daliri, Karbasi (2025). The original PolarQuant + QJL pipeline.

\- TurboQuant-MLX on PyPI: [https://pypi.org/project/turboquant-mlx-full](https://pypi.org/project/turboquant-mlx-full)

\- Nemotron-3-Super-120B-A12B-tq3a-tq2e-g32 on HuggingFace: [https://huggingface.co/manjunathshiva/Nemotron-3-Super-120B-A12B-tq3a-tq2e-g32](https://huggingface.co/manjunathshiva/Nemotron-3-Super-120B-A12B-tq3a-tq2e-g32) — the 48 GB-target model card, with full reproduction recipe.

\- TurboQuant-MLX: [https://github.com/manjunathshiva/turboquant-mlx](https://github.com/manjunathshiva/turboquant-mlx)

\- NVIDIA Nemotron-3-Super-120B-A12B-BF16: [https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16) — the original BF16 model from NVIDIA.

## Support

*If you found this article informative and valuable, I’d greatly appreciate your support:*

*“Give it a few claps 👏 on Medium to help others discover this content (did you know you can clap up to 50 times?). Your claps will help spread the knowledge to more readers.”*

- Share it with your network of AI enthusiasts and professionals.
- Subscribe to my YouTube channel for AI videos explained in simple English: [https://www.youtube.com/@AIBroEnglish](https://www.youtube.com/@AIBroEnglish)
- Connect with me on LinkedIn: [https://www.linkedin.com/in/manjunath-janardhan-54a5537/](https://www.linkedin.com/in/manjunath-janardhan-54a5537/)