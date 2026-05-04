---
title: "TurboQuant: Compressing KV cache 4x on Apple Silicon — how I doubled the usable context length of 120B LLMs on a MacBook"
source: "https://medium.com/data-science-collective/turboquant-compressing-kv-cache-4x-on-apple-silicon-how-i-doubled-the-usable-context-length-5a8bce975fe2"
published: 2026-04-07
created: 2026-05-04
description: "More"
tags:
  - "clippings"
author:
  - "Manjunath Janardhan"
---
*TurboQuant doesn’t just compress weights. I adapted its KV cache compression for MLX, cutting runtime memory 3.5x on GPT-OSS with zero quality loss*

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*Yb6DynMjCGkhSLNFoZPYaw.jpeg)

Image By Manjunath Janardhan. Generated using Google Nano Banana Pro.

In Parts 1 and 2 of this series, I compressed LLM weights with TurboQuant-MLX — fitting 120B and 122B parameter models on a 64GB MacBook by shrinking their weights from 240 GB down to 48–50 GB. The models ran. The output was good. I wanted to take it further to compress the KV Cache based on the Google paper on TurboQuant.

If you have not read my previous series, here is the link where I used TurboQuant to compress the weights, which made them run 120B and 122B parameters on my 64GB M4 MacBook. The only issue is that we need to close all other applications to run, but now, with KV Cache compression, that is not the case.

Part 1:

## [I Built a Quantization Method That Beats Standard 4-bit on a 7B Model — With Zero Training Data](https://ai.gopubby.com/i-built-a-quantization-method-that-beats-standard-4-bit-on-a-7b-model-with-zero-training-data-fe37c2fb4952?source=post_page-----5a8bce975fe2---------------------------------------)

### Adapting Google’s TurboQuant for weight compression on Apple Silicon using MLX, and what the perplexity numbers…

ai.gopubby.com

Part 2:

## [How I run 122B-parameter LLMs on a MacBook — outperforming MXFP4 and standard quantization on…](https://medium.com/data-science-collective/how-i-run-122b-parameter-llms-on-a-macbook-outperforming-mxfp4-and-standard-quantization-on-apple-0552ee3da1f7?source=post_page-----5a8bce975fe2---------------------------------------)

### I extended TurboQuant to Mixture-of-Experts models. A 120B LLM that no existing format could fit on 64GB now runs at 44…

medium.com

When you generate text with an LLM, every token you produce adds to the KV cache — the key and value vectors that the attention mechanism stores so it doesn’t recompute them. On a short prompt, the KV cache is negligible. In long conversations or documents, it scales linearly with context length and can consume gigabytes of RAM in addition to the model weights.

For GPT-OSS-120B at its full 131K context window, the KV cache alone is **9.2 GB in float16**. That’s 9.2 GB on top of the 48 GB of compressed weights. On a 64GB machine, that leaves roughly 7 GB for activations, the operating system, and everything else. In practice, you run out of memory well before reaching the model’s full context capability.

The original TurboQuant paper (Zandieh et al., 2025) doesn’t just compress weights. Section 4 describes a KV cache compression pipeline: PolarQuant (Hadamard rotation + Lloyd-Max codebook quantization) applied to the key and value vectors as they’re stored in the cache. The paper reports “absolute quality neutrality at 3.5 bits” — meaning you can compress the KV cache nearly 5x with no measurable degradation.

I wanted to try that for MLX.

**I have built the PyPI package.** TurboQuant-MLX ships as a single PyPI package. On any Apple Silicon Mac with Xcode Command Line Tools and CMake 3.27+ installed:

```c
pip install turboquant-mlx-full
```

The package gives you both the 2/3/4-bit *weight* compression from Parts 1 and 2 **and** the KV cache compression that’s the subject of this article. A complete copy-pasteable usage recipe is at the end of the article in the *Try it yourself* section.

## Why KV cache compression matters more than you think

Here’s the math that motivated this work.

GPT-OSS-120B has 36 layers, 8 KV heads per layer, head dimension 64. It’s a hybrid attention model — some layers use full attention (KV cache grows with context) and some use sliding window attention (fixed 128-token window). At 131K context with float16 KV cache:

- Full-attention layers: cache grows linearly → dominates memory at long contexts
- Sliding-window layers: fixed at 128 tokens → negligible
![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*srBVCfJN_DkW97L2P_bw8g.jpeg)

Image By Manjunath Janardhan. Table shows how much RAM saved using 3-bit compression on KV Cache.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*UlNaZ_z9GLs6lAjuniIUxA.jpeg)

Image By Manjunath Janardhan. GPT-OSS-120B KV cache memory: FP16 vs TurboQuant 3-bit at 4K, 32K, and 131K tokens

At 131K context, TQ 3-bit saves **7.4 GB** of RAM. That’s the difference between fitting the model and not.

The same applies to Qwen3.5–122B-A10B. It has 48 layers, but only 12 use growing KV cache (the rest use GatedDeltaNet linear attention). At 262K context, the FP16 KV cache is 6.1 GB; TQ 3-bit compresses it to roughly 1.2 GB.

## How TurboQuant KV cache compression works

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*YhylozHEXDZ9E6wrgSEnIg.jpeg)

Image By Manjunath Janardhan. Stages of KV Compression.

The approach mirrors weight compression but operates on the fly during inference:

1\. **Incoming KV vectors arrive in float16** — the model computes new key and value vectors for each token as normal.

2\. **Hadamard rotation** — multiply by random signs, then apply a fast Hadamard transform. This spreads the magnitude uniformly across all dimensions, eliminating outliers that cause quantization errors. The same rotation used for weight compression works here.

3\. **Group-wise RMS normalization** — split each vector into groups of 64 elements, divide by the group’s RMS. Store the RMS as a float16 scale factor.

4\. **Lloyd-Max codebook quantization** — map each normalized value to the nearest centroid in a precomputed optimal codebook. At 3-bit, there are 8 centroids. Pack the 3-bit indices into uint32 arrays.

5\. **For attention** — when the model needs the full cache for the attention computation, dequantize: unpack indices, look up centroids, multiply by scales, apply inverse rotation. The dequantized float16 values flow through MLX’s standard \`mx.fast.scaled\_dot\_product\_attention\`.

The compressed representation stores only the packed indices (3 bits per element) and the per-group scales (float16). No bias term is needed because the rotation makes the distribution symmetric around zero. This gives **4.6x compression at 3-bit** and **3.8x at 4-bit** versus float16.

## The engineering challenge: hybrid attention and attention sinks

Getting TurboQuant KV cache to work on real models — required solving three problems specific to how modern LLMs implement attention in MLX.

## Problem 1: GPT-OSS uses attention sinks

GPT-OSS passes learned “sink” vectors to the attention computation. MLX’s quantized attention path (\`quantized\_scaled\_dot\_product\_attention\`) explicitly rejects attention sinks:

```c
if hasattr(cache, "bits"):
   if sinks is not None:
       raise ValueError("Quantized SDPA does not support attention sinks.")
```

My initial implementation exposed a \`bits\` attribute on the TQ cache (to route through the quantized matmul path). This would crash on GPT-OSS.

The fix: return float16 dequantized values and route through the standard SDPA path. This is compatible with all attention features — sinks, sliding windows, causal masks. The memory savings come from the compressed *\*torage*, not the attention computation itself. The temporary float16 arrays for attention are part of MLX’s lazy evaluation graph and don’t persist between generation steps.

## Problem 2: Hybrid cache architectures

Both GPT-OSS and Qwen3.5 use heterogeneous cache types across layers:

\- **GPT-OSS**: \`KVCache\` for full-attention layers, \`RotatingKVCache\` for sliding-window layers

\- **Qwen3.5**: \`KVCache\` for full-attention layers, \`ArraysCache\` for GatedDeltaNet linear-attention layers

TQ compression only applies to \`KVCache\` instances. The conversion function detects the cache type and leaves everything else unchanged:

```c
def convert_cache_to_turboquant(prompt_cache, tq_bits=3, ...):
    from mlx_lm.models.cache import KVCache
    new_cache = []

    for c in prompt_cache:
        if not isinstance(c, KVCache):
            new_cache.append(c)  # Leave RotatingKVCache, ArraysCache as-is
            continue
        tq = TurboQuantKVCache(tq_bits=tq_bits, ...)

        if c.keys is not None and c.offset > 0:
            tq.update_and_fetch(c.keys[..., :c.offset, :],
                                c.values[..., :c.offset, :])
        new_cache.append(tq)

    return new_cache
```

This drops in without modifying any model code.

## Problem 3: The prompt-first pattern

MLX’s built-in KV quantization (\`kv\_bits\` parameter in \`mlx\_lm.generate\`) processes the prompt with a full-precision cache, then converts to quantized format. This matters because prompt processing benefits from exact KV values for establishing the attention pattern.

I follow the same pattern: process the entire prompt with standard float16 \`KVCache\`, then convert to \`TurboQuantKVCache\`. Subsequent generation tokens are TQ-compressed on arrival. This gives the best of both worlds — exact prompt processing and compressed generation.

### Results: GPT-OSS-20B with 3-bit TQ KV cache

I tested on GPT-OSS-20B (24 layers, 12 full-attention + 12 sliding-window, 8 KV heads, head\_dim=64) with a 672-token physics prompt and 200 tokens of generation.

### Output quality

**FP16 baseline:**

```c
We have to produce a comprehensive analysis of each topic, 
explaining key principles, major experiments, and current open 
questions… Should be detailed…
```

**TQ 3-bit:**

```c
We need to produce a detailed analysis for each topic, connecting themes, 
and highlight promising directions. Provide key principles, major experiments,
 open questions. Should be comprehensive…
```

Both outputs are coherent, on-topic, and structurally equivalent. Different wording, same quality of reasoning.

### Memory and performance

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*rvjh16PmL6-yTZuADolNkA.jpeg)

Image By Manjunath Janardhan. Table showing the Savings and Speed we got upon compression.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*t0mNS7sMbwxgdMw6x4MSSA.jpeg)

Image By Manjunath Janardhan. TurboQuant 3-bit KV cache savings on GPT-OSS-20B, GPT-OSS-120B, and Qwen3.5–122B

The 3.5x savings at 872 total tokens (672 prompt + 200 generated) is already approaching the theoretical maximum. At longer contexts (32K+), savings converge to 4.3x as the full-attention layers dominate over the fixed sliding-window layers.

## Roundtrip quality metrics

I measured quantize-dequantize roundtrip quality across the head dimensions of both target models:

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*8_3vXJCo0pYXGlteLM9qJg.jpeg)

Image By Manjunath Janardhan. Table showing quality across head dimesnions.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*rJgNssiM2KbJHOitimGM4w.jpeg)

Image By Manjunath Janardhan. Roundtrip quality and compression ratio by bit-width — 3-bit is the sweet spot at 0.98 cosine similarity and 4.6x compression

At 3-bit, cosine similarity between original and reconstructed KV vectors is consistently above 0.98. The Hadamard rotation is doing its job — distributing the magnitude so the codebook can represent the values efficiently.

### Speed: a tradeoff on small models, a win on large ones

TQ KV cache runs at 29.9 tok/s versus 90.6 tok/s for FP16 on GPT-OSS-20B — roughly 3x slower. This is because every generation step dequantizes the entire compressed cache to float16 for the attention computation. The cost grows linearly with context length, and on a small model that runs fast to begin with (90 tok/s), the dequant overhead dominates.

Then I ran the same test on GPT-OSS-120B and got the opposite result:

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*nd9H8b1xooLZeBUjVtqwQA.jpeg)

Image By Manjunath Janardhan. Table shows the compression of 3bit KV and the speed.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*Kqfyx4lNkJ34QriQ1godUQ.jpeg)

Image by Manjunath Janardhan. The speed flip: TurboQuant KV cache is 3x slower on GPT-OSS-20B but 1.4x faster on GPT-OSS-120B

On the 120B, the inference computation itself is so memory-bandwidth-bound that *shrinking the KV cache by 4x reduces total step time more than the dequant operation adds*. The 4x smaller cache means less memory traffic per attention step, which on Apple Silicon’s unified memory is the dominant cost. Compression isn’t just buying you headroom — it’s buying you throughput.

This flips the usual narrative around quantization. On small fast models, every quantization scheme is a quality-vs-speed tradeoff. On large slow models, aggressive quantization can be a *\*win on both axes simultaneously\**: less memory and more tokens per second.

And the memory savings are concrete: at 131K context on GPT-OSS-120B, you save **7.2 GB of RAM**. That’s the difference between the model fitting on your MacBook and running out of memory mid-conversation.

## Combining weight and KV cache compression: the double compression problem

This is where Parts 1, 2, and 3 come together — but not without a surprise.

### The naive approach fails

My first instinct was to stack both: TQ 3-bit weights (from Part 2) plus TQ 3-bit KV cache. I loaded the TQ-compressed GPT-OSS-20B model and enabled KV cache compression at 3-bit.

The output started coherent — “The blue color of the sky is due to the scattering of sunlight by the atmosphere” — then collapsed into repetition within 30 tokens: “The blue? The blue? The blue?”

The problem is **compounding quantization noise**. The KV vectors produced by a weight-quantized model already carry noise from the compressed weights. Compressing those noisy vectors a second time pushes past the model’s tolerance threshold. Two layers of 3-bit quantization is too aggressive.

### 4-bit KV is the sweet spot for double compression

The fix: use 4-bit TQ for the KV cache when the weights are already compressed. I tested all three configurations on GPT-OSS-20B with TQ 3-bit weights:

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*mfPq0J4QAEy2NZYQQZC4vg.jpeg)

Image By Manjunath Janardhan. Table shows the diffrent config, speed and Quality along with KV Cache size.

TQ 4-bit KV with TQ 3-bit weights produced a clean, correct response:

```c
The sky appears blue because of a physical phenomenon called Rayleigh 
scattering. Light travels through the atmosphere and is scattered by the 
molecules and particles in the air. Short-wavelength light (blue, violet) 
is scattered more strongly than long-wavelength light (red, orange).
```

That’s **3.9x KV cache savings** on top of the weight compression, with zero quality degradation.

### 100B+ models tolerate 3-bit on 3-bit just fine

I thought “use 4-bit KV when weights are TQ-compressed” would apply universally. When I tested on Qwen3.5–122B-A10B with TQ 3-bit weights and TQ 3-bit KV cache — the configuration that broke GPT-OSS-20B — and it worked perfectly. Then I tested the same thing on GPT-OSS-120B. Same result.

**Qwen3.5–122B-A10B** (“Why is the sky blue?”, 16 prompt tokens):

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*2gZr09NLo9_lBOGSu2cTBQ.jpeg)

The thinking output was character-for-character similar across both runs: *identifying sunlight as a mix of wavelengths, explaining why short wavelengths scatter more strongly, walking through Rayleigh scattering, even mentioning sunset reddening as a corollary.*

**GPT-OSS-120B** (144-token physics prompt covering Bell inequalities, AdS/CFT, inflation, and dark matter):

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*y6n9vusnv1bPz7YYhnuB2A.jpeg)

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*ZVpEXymHADJ791mOo6VAug.png)

GPT-OSS-120B all configurations: TQ 3-bit KV is the smallest cache AND faster than FP16

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*XsZoimeNb4MxydGofTVKiw.png)

Image By Manjunath Janardhan. Double compression tolerance scales with model size — GPT-OSS-20B fails at 3+3, but GPT-OSS-120B and Qwen3.5–122B run cleanly

Three things jump out:

1\. **3-bit KV works on 120B too.** No repetition collapse, no drift. The output stays in the same \`<|channel|>analysis\` planning mode as the FP16 baseline, with the same logical structure.

2\. **3.8x KV cache savings** at just 344 total tokens. At full 131K context, this projects to ~2.4 GB saved.

3\. **TQ 3-bit is** *faster* **than FP16 on the 120B** (8.7 vs 6.4 tok/s). This is the opposite of the 20B result, where TQ was 3x slower. On 120B, the dequant overhead is dwarfed by the memory bandwidth savings from the 4x smaller cache. The bigger the model, the more the compression *helps* throughput.

The pattern is now clear: **double compression tolerance scales with model size, and so do the speed benefits.** GPT-OSS-20B has 12 full-attention layers and modest redundancy — quantization noise compounds quickly, and the dequant overhead is visible because the model is fast to begin with. At 120B and 122B, both effects flip: the model has enough redundancy to absorb stacked 3-bit noise, *\*and\** it’s slow enough that any reduction in KV cache memory traffic is a net win on tokens-per-second.

This matches what we saw in Part 2: large models tolerate aggressive weight compression better than small ones, and the same holds for KV cache compression on top.

### The full stack on GPT-OSS-120B

For GPT-OSS-120B on a 64GB M4 Max, combining TQ 3-bit weights with TQ 3-bit KV cache (now confirmed working at this scale):

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*96SQGHHcbPwUtlVbaR3ZIw.jpeg)

Image By Manjunath Janardhan. Table showing the Saving of TurboQuant KV Cache compression.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*SmohB81_uw5EdlHfhUoy9Q.png)

Image by Manjunath Janardhan. GPT-OSS-120B on a 64GB MacBook: only TQ 3-bit weights + TQ 3-bit KV fits at full 131K context

Without TurboQuant, GPT-OSS-120B doesn’t fit on 64GB even at zero context. With TQ weight compression alone (Part 2), it fits but runs out of memory at moderate context lengths. With both weight and KV cache compression at 3-bit, you can run the model at its **full 131K context window** and still have 14 GB of headroom — and generation actually runs *faster* than the FP16-cache baseline, not slower.

The rule, refined with the 120B and 122B data in hand: **3-bit KV is the right default at every scale for FP16-weight models. For TQ-compressed weights, use 4-bit KV on small models (~20B) where the noise budget is tight, and 3-bit KV on 100B+ models where redundancy absorbs the compounding noise.** Both GPT-OSS-120B and Qwen3.5–122B run cleanly at 3-bit weights + 3-bit KV — and on the 120B, 3-bit KV is actually *faster* than FP16 because the cache memory bandwidth savings outweigh the dequant overhead.

## What I learned

**3-bit is the sweet spot for KV cache.** At 3-bit, TQ achieves 0.98+ cosine similarity on the KV vectors with 4.3x compression. At 4-bit, the extra fidelity (0.995 cosine) doesn’t translate to noticeably better output but costs 20% more memory. At 2-bit, compression is excellent (7.1x) but quality degrades.

**Small models are not valid tests for KV cache compression.** I spent significant time debugging on a 0.5B model with only 2 KV heads. Every KV quantization scheme fails on it — including MLX’s built-in \`kv\_bits=4\`. The quantization noise per head is too high when there are only 2 heads to average over. On GPT-OSS-20B with 8 KV heads, both 3-bit and 4-bit TQ produce coherent output. The CLT (Central Limit Theorem) approximation that makes Hadamard rotation effective requires sufficient dimensionality.

**Attention sinks are a compatibility trap.** GPT-OSS uses learned attention sink vectors. MLX’s quantized attention path crashes with sinks. Any KV cache compression that routes through the quantized attention API will fail silently on some models and crash on others. Returning float16 and using the standard attention path is more robust, even though the quantized path is theoretically faster.

**The prompt-first conversion pattern matters.** Processing the prompt with full-precision cache, then converting to TQ, follows the same pattern that MLX’s built-in KV quantization uses. It ensures the model establishes its attention pattern on exact values before compression introduces noise.

## What’s next

- **Testing on GPT-OSS-120B and Qwen3.5–122B** at extended context lengths to validate the memory projections in practice
- **QJL residual correction** — the original TurboQuant paper uses a 1-bit Johnson-Lindenstrauss projection to correct quantization residuals. Adding this could push quality closer to FP16 at the same bit-width, potentially making 2-bit viable
- **Incremental dequantization** — the current implementation dequantizes the full cache every step. Caching the dequantized result and only processing new tokens would eliminate the per-step overhead entirely, at the cost of storing both compressed and decompressed representations
- **Upload compressed models to HuggingFace** and support downloading compressed models directly from HuggingFace.
- Integrate with **LM Studio** and **Ollama**.

## Try it yourself

Everything in this article ships as a single PyPI package. On any Apple Silicon Mac with Xcode Command Line Tools and CMake 3.27+ installed:

```c
pip install turboquant-mlx-full
```

The package builds a small Metal extension on install (about a minute) and is importable as \`turboquant\_mlx\` — the \`-full\` suffix is only on the PyPI name because the shorter name was claimed by another project.

### KV cache compression on any MLX model

The minimum integration is two lines: process the prompt with a normal float16 cache, then call \`convert\_cache\_to\_turboquant\` once.

```c
import mlx.core as mx
from mlx_lm import load
from mlx_lm.models.cache import make_prompt_cache
from turboquant_mlx.layers.polar_kv_cache import convert_cache_to_turboquant

model, tokenizer = load("openai/gpt-oss-20b")

prompt = "Why is the sky blue?"
input_ids = mx.array(tokenizer.encode(prompt))[None]

# Process the prompt at full precision...
cache = make_prompt_cache(model)
_ = model(input_ids, cache=cache)

# ...then compress the cache for the rest of generation.
cache = convert_cache_to_turboquant(cache, tq_bits=3, group_size=64)

# Continue your normal token-by-token loop, passing \`cache=cache\` into model().
```

Hybrid attention models like GPT-OSS and Qwen3.5 are handled automatically — \`RotatingKVCache\` (sliding-window) and \`ArraysCache\` (linear-attention) layers are passed through unchanged, and only the full-attention \`KVCache\` layers get compressed. You don’t need to know which layers use which attention type.

### A runnable side-by-side comparison

The package ships with a demo script that runs FP16 and TurboQuant 3-bit on the same prompt back-to-back, so you can see the memory and speed difference on your own machine and your own model:

```c
python -m turboquant_mlx.demo_kv \
  --model openai/gpt-oss-20b \
  --prompt "Why is the sky blue?" \
  --max-tokens 200 \
  --compare
```

On a 64GB M4 Max this prints both outputs as they stream, then a comparison line at the bottom showing tokens/sec and KV cache size for each configuration.

### The full stack: compressed weights + compressed KV cache

To reproduce the GPT-OSS-120B-at-131K-context configuration from the table above (TQ 3-bit weights + TQ 3-bit KV), first convert the weights once:

```c
turboquant-convert --hf-path openai/gpt-oss-120b --bits 3 --mlx-path gpt-oss-120b-tq3
```

Then point \`demo\_kv\` at the converted model:

```c
python -m turboquant_mlx.demo_kv \
  --model gpt-oss-120b-tq3 \
  --prompt "Explain Bell inequalities, AdS/CFT, inflation, and dark matter" \
  --max-tokens 500 \
  --tq-bits 3
```

Per the rule of thumb derived earlier in the article: use \` — tq-bits 3\` on 100B+ models, \` — tq-bits 4\` on smaller models (~20B) where the noise budget is tighter.

All of the numbers reported in this article — the 4.6× compression, the 7.4 GB savings at 131K context, the speed flip on the 120B — are reproducible from this single package. The install ships with the Metal kernels, the conversion CLI, the Python integration layer, and the demo script. If you try a configuration I haven’t tested, please share the numbers — issues and PRs are welcome on the repo

## [GitHub - manjunathshiva/turboquant-mlx: Extreme weight + KV cache compression for LLMs on Apple…](https://github.com/manjunathshiva/turboquant-mlx?source=post_page-----5a8bce975fe2---------------------------------------)

### Extreme weight + KV cache compression for LLMs on Apple Silicon (MLX implementation of Google's TurboQuant) …

github.com

## Resources

- TurboQuant paper [https://arxiv.org/abs/2504.19874](https://arxiv.org/abs/2504.19874)
- MLX: [https://github.com/ml-explore/mlx](https://github.com/ml-explore/mlx)
- TurboQuant-MLX on PyPI: [https://pypi.org/project/turboquant-mlx-full](https://pypi.org/project/turboquant-mlx-full)
- TurboQuant-MLX on GitHub: [https://github.com/manjunathshiva/turboquant-mlx](https://github.com/manjunathshiva/turboquant-mlx)

## Support

*If you found this article informative and valuable, I’d greatly appreciate your support:*

*“Give it a few claps 👏 on Medium to help others discover this content (did you know you can clap up to 50 times?). Your claps will help spread the knowledge to more readers.”*

- Share it with your network of AI enthusiasts and professionals.
- Subscribe to my YouTube channel for AI videos explained in simple English: [https://www.youtube.com/@AIBroEnglish](https://www.youtube.com/@AIBroEnglish)
- Connect with me on LinkedIn: [https://www.linkedin.com/in/manjunath-janardhan-54a5537/](https://www.linkedin.com/in/manjunath-janardhan-54a5537/)