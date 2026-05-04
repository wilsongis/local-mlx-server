---
title: "How I run 122B-parameter LLMs on a MacBook — outperforming MXFP4 and standard quantization on Apple Silicon"
source: "https://medium.com/data-science-collective/how-i-run-122b-parameter-llms-on-a-macbook-outperforming-mxfp4-and-standard-quantization-on-apple-0552ee3da1f7"
published: 2026-04-06
created: 2026-05-04
description: "More"
tags:
  - "clippings"
author:
  - "Manjunath Janardhan"
---
*I extended TurboQuant to Mixture-of-Experts models. A 120B LLM that no existing format could fit on 64GB now runs at 44 tokens per second on an M4 Max*

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*zwWy8NTHGgd3aM1sM-oSBQ.jpeg)

Image by Manjunath Janardhan. Generated using Google Nano Banana Pro 2.

Last time I published an article about TurboQuant-MLX — a model compression technique that adapts Google’s TurboQuant for LLM weight quantization on Apple Silicon using MLX. The results on dense models (1B to 7B) were solid: usable 2-bit quantization where standard affine completely broke down, and measurably better quality at every bit-width above 3B parameters.

## [I Built a Quantization Method That Beats Standard 4-bit on a 7B Model — With Zero Training Data](https://ai.gopubby.com/i-built-a-quantization-method-that-beats-standard-4-bit-on-a-7b-model-with-zero-training-data-fe37c2fb4952?source=post_page-----0552ee3da1f7---------------------------------------)

### Adapting Google’s TurboQuant for weight compression on Apple Silicon using MLX, and what the perplexity numbers…

ai.gopubby.com

The most common question I got: Does this work on Mixture-of-Experts (MoE) large language models?

MoE architectures like Mixtral, Qwen-MoE, and OpenAI’s GPT-OSS family are where LLM quantization and model compression matter most. These models have 14B to 122B total parameters, but activate only a fraction per token. You need all those expert weights in memory, even though most sit idle for any given input. If you can’t compress them, you can’t run them on consumer hardware.

I spent the last few days extending TurboQuant for MoE. I tested on four models, scaling from 14B to 122B parameters. The results surprised me — especially when TurboQuant beat the MXFP4 format that OpenAI ships GPT-OSS in.

## What makes Mixture-of-Experts LLM quantization different

In a dense transformer, every linear layer gets the same treatment: rotate the weights, apply the codebook, done. In an MoE model, each transformer layer has a router that picks which experts to use, plus dozens or hundreds of separate expert FFN modules, each with their own weight matrices.

GPT-OSS-20B has 32 experts per layer, each with 3 projections across 24 layers — that’s 2,304 separate expert weight matrices of size 2880x2880. Qwen3.5–122B scales this further to 256 experts per layer across 48 layers.

Three challenges I had to solve:

1\. GPT-OSS uses a hidden size of 2880. TurboQuant needs Hadamard-compatible dimensions. I split each dimension into 9 blocks of 320 and apply the transform to each block independently — mathematically equivalent to a block-diagonal Hadamard matrix.

2\. I created \`PolarQuantizedSwitchLinear\`, a layer that stores expert weights as 3D packed arrays. All experts within a layer share the same rotation signs and codebook, since after Hadamard rotation each expert’s weight distribution is approximately Gaussian.

3\. OpenAI doesn’t distribute GPT-OSS in FP16. The expert weights come in MXFP4 format (4-bit with shared microscaling exponents). I had to dequantize MXFP4 to float, then re-quantize with TurboQuant. Double quantization isn’t ideal, but it’s the only option when original weights aren’t available.

## Results: beating MXFP4 on GPT-OSS-20B

OpenAI’s GPT-OSS-20B is a 21B-parameter MoE model (32 experts, 4 active per token). It ships in MXFP4 format. Since there are no FP16 weights, the comparison is: original MXFP4 vs TurboQuant applied to dequantized MXFP4 weights.

I wasn’t expecting TurboQuant to work here. You can’t recover information that MXFP4 already lost, and re-quantizing should only make things worse.

But I was wrong.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*EBiChMkVvXno-38vxfwCzQ.png)

GPT-OSS-20B perplexity and model size comparison. TurboQuant achieves lower perplexity than OpenAI’s MXFP4 quantization at every bit-width while being smaller. Source: My benchmarks on Apple M4 Max 64GB

TurboQuant 4-bit achieved 12.5% lower perplexity (72.63 vs 83.04) and was 13% smaller than the original MXFP4 model. TurboQuant 3-bit achieved 5.3% lower perplexity and was 28% smaller.

Why does this happen? MXFP4 uses a shared exponent per group of 32 values — efficient for hardware but suboptimal for the actual weight distribution. When we dequantize to float and apply TurboQuant (Hadamard rotation to Gaussianize, followed by Lloyd-Max codebooks that are information-theoretically optimal for Gaussians), we’re fitting a better quantization scheme to the same data. The codebook places reconstruction levels where the density actually is.

The practical implication: if you’re running GPT-OSS-20B on Apple Silicon and you care about quality, TurboQuant 4-bit gives you better output from a smaller model than the format OpenAI shipped.

## GPT-OSS-120B: running a 120-billion parameter LLM locally on a 64GB RAM M4 MacBook

OpenAI’s GPT-OSS-120B has 128 experts, 4 active per token, 36 layers. The original MXFP4 weights are 63.5 GB. That does not fit on a 64GB M4 Max once you account for KV cache and activations. Neither does the mlx-community’s affine 4-bit re-quantization at 65.8 GB. You cannot run this model in any existing format on consumer hardware.

TurboQuant 3-bit compresses it to 48 GB. With 52 GB peak memory during generation, it fits on a 64GB machine with room to breathe. And it generates at 44 tokens per second.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*4Xy_65LPNbDcqA_abl91Nw.png)

GPT-OSS-120B model size comparison: no existing quantization format fits on 64GB RAM. TurboQuant 3-bit (48 GB) is the only way to run this 120B LLM on consumer Apple Silicon hardware. My benchmarks on Apple M4 Max 64GB.

At 2-bit (32 GB), the model fits comfortably and generates at 51 tok/s, but output quality degrades rapidly — confirming 3-bit as the minimum for coherent generation on pre-quantized MoE models.

## The Metal kernel that changed everything: a 43x inference speedup

My initial MoE implementation dequantized all 32 expert weight matrices at every forward pass, then used \`mx.gather\_mm\`. Only 4 experts are active per token, so I was doing 8x more work than necessary. I wrote fused Metal kernels that read packed weights directly for just the selected experts.

But I missed something important. The gate and up projections share a single input vector across all selected experts — my \`polar\_gather\_qmv\` kernel handled that fine. The down projection receives a different input vector per expert (each expert’s activation is different after the non-linearity). My layer code detected the multi-input case and fell back to dequantizing all experts — materializing 530 MB of float16 weights per layer, 24 layers per token. That’s 12.7 GB of wasted memory allocation per generated token. On a model that’s only 9.3 GB total.

Once I spotted this, I wrote \`polar\_multi\_gather\_qmv\`. The diff was one line of Metal code (\`x\[col\]\` became \`x\[expert\_local \* in\_dims + col\]\`), but the impact was enormous.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*WZPAmgDtqVSo4tvgkfAM5A.png)

LLM generation speed before and after the fused MoE Metal kernel fix. One data access pattern change yielded a 43x inference speedup on Apple M4 Max. My benchmarks on Apple M4 Max 64GB.

Generation went from 1.7 tok/s to 73 tok/s. A 43x speedup from fixing one data access pattern.

## Qwen3.5–122B: running a 122B thinking LLM on Apple Silicon with 64GB RAM

After the GPT-OSS results, I wanted to test on a completely different architecture. Qwen3.5–122B-A10B is a 122B-parameter MoE model with 256 experts (8 active per token), hybrid attention mixing GatedDeltaNet (linear attention) with standard softmax attention, a shared expert per layer, and built-in thinking/reasoning capability.

The original BF16 weights are approximately 240 GB — nearly 4x larger than 64 GB RAM. TurboQuant 3-bit compressed it to approximately 50 GB. It fits. And it generates at 26.5 tokens per second.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*i6A1fvfOQx71T2RHPiorJQ.png)

Qwen3.5–122B-A10B: 240 GB LLM compressed to 50 GB with 3-bit quantization. Generates at 26.5 tok/s on Apple M4 Max with full reasoning capability preserved. My benchmarks on Apple M4 Max 64GB.

What makes this result significant beyond the raw numbers:

- 256 experts is double GPT-OSS-120B’s 128. The converter’s memory-efficient processing was essential; an earlier version ran out of memory.
- Hybrid GatedDeltaNet + softmax attention is a completely different attention pattern from anything I had tested. TurboQuant required zero architecture-specific changes beyond adding the model type to the configuration.
- The 4.8x compression ratio (240 GB to 50 GB) is the largest I have achieved.
- Conversion completed in 90 seconds — 144 SwitchLinear layers (256 experts each) plus 373 Linear layers quantized in under two minutes.

## Benchmark results: all MoE models compared on Apple M4 Max

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*CjmqUQ59SWftST4Y-8pEQQ.png)

TurboQuant 3-bit generation speed across all MoE LLMs tested on Apple M4 Max 64GB. All models run interactively on a single MacBook with Apple Silicon. My benchmarks on Apple M4 Max 64GB.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*x86idtVsQGh_RY6_PNBmCQ.png)

Speed vs compressed size for all MoE LLM configurations tested. TurboQuant 3-bit is the only quantization method that enables running 100B+ models on 64GB Apple Silicon. My benchmarks on Apple M4 Max 64GB.

## Key takeaways: what I learned about MoE model compression

A few things that were not obvious until I tried them.

Expert weights Gaussianize just like dense weights. The Hadamard rotation operates on individual weight matrices regardless of architecture — the math doesn’t care whether the matrix belongs to a shared layer or expert number 47.

Shared rotation signs across experts work fine. Sharing signs across all experts in a layer simplifies storage (one signs vector per layer instead of per-expert) and gives identical quality. The codebook is already shared since it’s a mathematical constant.

2-bit works for benchmarks, not for generation. The perplexity numbers at 2-bit looked reasonable. The single-step predictions were sensible. But when I actually generated text, it fell apart within 20 tokens. Small errors compound through the attention mechanism during autoregressive decoding, and over a sequence of tokens, it snowballs. 3-bit is the sweet spot for MoE on consumer hardware.

The MXFP4 finding was the real surprise. Finding that a better quantization scheme can compensate for double-quantization quality loss suggests that the format matters more than the number of quantization stages. This has implications beyond my project: a general strategy of “dequant and requant with a better scheme” could improve any model distributed in a suboptimal format.

## What’s next for on-device LLM inference

- Fused multi-projection kernels to reduce scheduling overhead further
- Head-to-head comparison with GPTQ and AWQ on MoE models
- Better 2-bit compression with improved residual correction schemes

The code will be open-sourced soon.

## Support

*If you found this article informative and valuable, I’d greatly appreciate your support:*

*“Give it a few claps 👏 on Medium to help others discover this content (did you know you can clap up to 50 times?). Your claps will help spread the knowledge to more readers.”*

- Share it with your network of AI enthusiasts and professionals.
- Subscribe to my YouTube channel for AI videos explained in simple English: [https://www.youtube.com/@AIBroEnglish](https://www.youtube.com/@AIBroEnglish)
- Connect with me on LinkedIn: [https://www.linkedin.com/in/manjunath-janardhan-54a5537/](https://www.linkedin.com/in/manjunath-janardhan-54a5537/)