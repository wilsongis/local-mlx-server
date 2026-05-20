---
title: "Graphify vs. Caveman: Two Clever Tools That Make Your AI Coding Assistant Way Smarter"
source: "https://medium.com/@shahsoumil519/graphify-vs-caveman-two-clever-tools-that-make-your-ai-coding-assistant-way-smarter-c6cd91378c59"
published: 2026-04-21
created: 2026-05-20
description: "More"
tags:
  - "clippings"
author:
  - "Soumil Shah"
---
*One builds a map of your entire codebase. The other makes your AI talk like a prehistoric human. Both are genuinely useful — and one is dramatically more popular than the other.*

**Video Guide**

You open your AI coding assistant. You ask it to help you trace a bug through your codebase. It reads a dozen files, produces a wall of text, and burns through your token budget before getting to the actual answer.

Two open-source projects have become surprisingly popular by attacking this problem from opposite directions. **Graphify** makes your AI smarter about your code. **Caveman** makes your AI talk less. Both have tens of thousands of GitHub stars — but for very different reasons.

Let’s break down what they actually are, how they work, and when to use which.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*gwrzPw9vAZRLXwk_uyGfXw.png)

## What is Graphify?

Imagine you dropped a paper map of a city into a shredder, then tried to navigate by reading every shred one at a time. That’s roughly how an AI coding assistant reads a large codebase without help — file by file, query by query, with no sense of the whole.

Graphify fixes this. You run one command — `/graphify .` — in your project folder. It reads every file (code, docs, PDFs, images, even videos), builds a connected knowledge graph of concepts and relationships, and gives your AI a compact map to navigate from.

```c
# Run it once on any folder
pip install graphifyy && graphify install
# Then in your coding assistant:
/graphify .

# Output:
graphify-out/
├── graph.html ← interactive clickable graph
├── GRAPH_REPORT.md ← plain-English summary for your AI
├── graph.json ← queryable graph (weeks later, still works)
└── cache/ ← only re-runs changed files
```

The key insight is what happens next. On a corpus of 52 files (code + papers + images), Graphify reduces tokens per query by **71.5×**. Your AI is no longer reading the raw files — it’s reading a compact structural summary and querying specific parts of the graph only when needed.

> *“Graphify is the answer to Andrej Karpathy’s /raw folder problem — a place to drop papers, tweets, screenshots, and notes and actually be able to query them later.”*

It supports 23 programming languages via AST parsing, handles multimodal input (code, PDFs, images, video), and tags every extracted relationship as either EXTRACTED (found directly) or INFERRED (a reasonable guess, with a confidence score). You always know what was found versus guessed.

## What is Caveman?

Caveman starts from a different observation: AI coding assistants are *extremely wordy*. Ask Claude why your React component is re-rendering, and you get a four-paragraph explanation with acknowledgments, caveats, context, and a polite summary. You needed two sentences and a code fix.

Caveman makes your AI talk like a prehistoric human. That’s the entire pitch. Type `/caveman` in Claude Code and responses immediately compress — dropping articles, filler words, pleasantries, and hedging, while keeping every technical detail intact.

**BEFORE / AFTER — SAME QUESTION, SAME ANSWER**

**Normal**: The reason your React component is re-rendering is likely because you’re creating a new object reference on each render cycle. When you pass an inline object as a prop, React’s shallow comparison sees it as a different object every time, which triggers a re-render. I’d recommend using useMemo to memoize the object.

69 tokens

**Caveman:**

New object ref each render. Inline object prop = new ref = re-render. Wrap in \`useMemo\`

**19 tokens — 72% fewer**

Across benchmarks on real prompts, Caveman cuts output tokens by an average of 65%, with some tasks saving over 85%. And here’s the surprising part: research published in early 2026 found that constraining models to brief responses actually *improved* accuracy by 26 percentage points on certain benchmarks. Less word can mean more correct.

Caveman comes with four intensity levels — Lite (drop filler, keep grammar), Full (default caveman grunt), Ultra (telegraphic, abbreviate everything), and a 文言文 (Wenyan) mode using Classical Chinese for maximum compression. It also ships sub-skills: `/caveman-commit` for terse conventional commits, `/caveman-review` for one-line PR comments, and `/caveman:compress` to compress your CLAUDE.md file so even your session instructions use fewer tokens.

## Head-to-head: what are they actually solving?

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*XsZRpUGXzyCo_vqAfFynEw.png)

## When to use which

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*YinDPNwW2-sm7bhUQ7hjqQ.png)

The short version: use **Graphify** when you need your AI to be smarter about what your code means. Use **Caveman** when you need your AI to shut up and get to the point. They solve different problems — and they actually work great together.

## A real example: using them together

Here’s a scenario where both tools complement each other. You’re onboarding to a new Python service — maybe 40 files, some architecture docs, a few design decision PDFs.

```c
# Step 1: Build the knowledge graph once
/graphify ./myproject
# → Builds graph.json, GRAPH_REPORT.md, interactive HTML

# Step 2: Turn on caveman for the session
/caveman full

# Step 3: Ask architecture questions
You: "How does authentication flow through this service?"
AI (caveman): AuthService → JWTMiddleware → UserRepo. Token expiry check in middleware.py:42. Refresh via /auth/refresh endpoint. No session state — stateless JWT.
```

Graphify handled the input side — the AI navigated via the graph instead of reading 40 raw files. Caveman handled the output side — the answer came back in four sentences instead of four paragraphs. Together, you saved tokens on both ends of the conversation.

## Verdict

Neither tool is magic. Graphify won’t untangle a genuinely messy codebase. Caveman won’t fix bad answers — it just makes bad answers shorter. But for developers who live in AI coding assistants all day, both are worth the five-minute setup.

Start with Caveman this afternoon. Come back to Graphify when you hit a codebase that feels too large to navigate. You’ll know when you need it.