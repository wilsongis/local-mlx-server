---
title: "Open WebUI: Self-Hosted LLM Interface"
source: "https://medium.com/@rosgluk/open-webui-self-hosted-llm-interface-0e4c7565542d"
published: 2026-01-11
created: 2026-05-24
description: "More"
tags:
  - "clippings"
author:
  - "Rost Glukhov"
---
[Open WebUI](https://www.glukhov.org/post/2026/01/open-webui-overview-quickstart-and-alternatives/) is a powerful, extensible, and feature-rich self-hosted web interface for interacting with large language models.

It supports [Ollama](https://www.glukhov.org/post/2024/12/ollama-cheatsheet/) and any OpenAI-compatible API, bringing the familiar ChatGPT experience to your infrastructure with complete privacy, offline capability, and enterprise-grade features.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/0*TOQcquWv3Iq6ccwS.png)

While Open WebUI is commonly used with Ollama (and is sometimes informally called an “Ollama WebUI”), it’s actually a backend-agnostic platform. It can connect to Ollama’s API for local model execution, but it also supports any OpenAI-compatible endpoint — including vLLM, LocalAI, LM Studio, Text Generation WebUI, and even cloud providers. This flexibility makes Open WebUI a comprehensive solution supporting multiple backends, RAG (Retrieval-Augmented Generation) for document chat, multi-user authentication, voice capabilities, and extensive customization options. Whether you’re running models on a laptop, a home server, or a Kubernetes cluster, Open WebUI scales to meet your needs.

## Quick Installation Guide

The fastest way to get started with Open WebUI is using Docker. This section covers the most common deployment scenarios.

## Basic Installation (Connecting to Existing Ollama)

If you already have Ollama running on your system, use this command:

```sh
docker run -d \
  -p 3000:8080 \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

This runs Open WebUI on port 3000, persisting data in a Docker volume. Access it at

[http://localhost:3000](http://localhost:3000/)

## Bundled Installation (Open WebUI + Ollama)

For a complete all-in-one setup with Ollama included:

```sh
docker run -d \
  -p 3000:8080 \
  --gpus all \
  -v ollama:/root/.ollama \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:ollama
```

The `--gpus all` flag enables GPU access for faster inference. Omit it if you’re running CPU-only.

## RAG and Document Chat

Open WebUI’s RAG implementation allows you to upload documents and have the model reference them in conversations. The system automatically chunks documents, generates embeddings, stores them in a vector database, and retrieves relevant context when you ask questions.

**Supported formats**: PDF, DOCX, TXT, Markdown, CSV, and more through built-in parsers.

**Usage**: Click the ‘+’ button in a chat, select ‘Upload Files’, choose your documents, and start asking questions. The model will cite relevant passages and page numbers in its responses.

**Configuration**: You can adjust chunk size, overlap, embedding model, and retrieval parameters in the admin settings for optimal performance with your document types.

## Multi-User Authentication and Management

Open WebUI includes a complete authentication system suitable for team and organizational use:

- **Local authentication**: Username/password with secure password hashing
- **OAuth/OIDC integration**: Connect to existing identity providers (Google, GitHub, Keycloak, etc.)
- **LDAP/Active Directory**: Enterprise directory integration
- **Role-based access**: Admin (full control), User (standard access), Pending (requires approval)

Admins can manage users, monitor usage, configure model access per user/group, and set conversation retention policies.

## Voice Input and Output

Built-in support for voice interaction makes Open WebUI accessible and convenient:

- **Speech-to-text**: Uses Web Speech API or configured external STT services
- **Text-to-speech**: Multiple TTS engines supported (browser-based, Coqui TTS, ElevenLabs, etc.)
- **Language support**: Works with multiple languages depending on your TTS/STT configuration

## Prompt Engineering Tools

Open WebUI provides robust tools for [prompt management](https://dasroot.net/posts/2026/01/ollama-system-prompts-temperature-tuning-guide/):

- **Prompt library**: Save frequently used prompts as templates
- **Variables and placeholders**: Create reusable prompts with dynamic content
- **Prompt sharing**: Share effective prompts with your team
- **Prompt versioning**: Track changes and improvements over time

## Model Management

Easy model switching and management through the UI:

- **Model catalog**: Browse and pull models directly from Ollama’s library
- **Custom models**: Upload and configure custom GGUF models
- **Model parameters**: Adjust temperature, top-p, context length, and other sampling parameters per conversation
- **Model metadata**: View model details, size, quantization, and capabilities

## Configuration and Customization

## Environment Variables

Key configuration options via environment variables:

```sh
# Backend URL (Ollama or other OpenAI-compatible API)
OLLAMA_BASE_URL=http://localhost:11434
```
```c
# Enable authentication
WEBUI_AUTH=true# Default user role (user, admin, pending)
DEFAULT_USER_ROLE=pending# Enable user signup
ENABLE_SIGNUP=true# Admin email (auto-create admin account)
WEBUI_ADMIN_EMAIL=admin@example.com# Database (default SQLite, or PostgreSQL for production)
DATABASE_URL=postgresql://user:pass@host:5432/openwebui# Enable RAG
ENABLE_RAG=true# Embedding model for RAG
RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## Connecting to Alternative Backends

Open WebUI works with any OpenAI-compatible API. Configure the base URL in Settings → Connections:

- **vLLM**: `http://localhost:8000/v1`
- **LocalAI**: [http://localhost:8080](http://localhost:8080/)
- **LM Studio**: `http://localhost:1234/v1`
- **Text Generation WebUI**: `http://localhost:5000/v1`
- **OpenAI**: `https://api.openai.com/v1` (requires API key)
- **Azure OpenAI**: Custom endpoint URL

## Open WebUI Alternatives

While Open WebUI excels at providing a self-hosted interface with strong [Ollama integration](https://glukhov.au/posts/2024/llms/), several alternatives offer different approaches to the same problem space. Your choice depends on whether you need multi-provider flexibility, specialized document handling, extreme simplicity, or enterprise features.

**LibreChat** stands out as the most provider-agnostic solution, offering native support for OpenAI, Anthropic, Azure OpenAI, Google Vertex AI, AWS Bedrock, and Ollama in a single interface. Its plugin architecture and enterprise features like multi-tenancy, detailed access controls, and usage quotas make it ideal for organizations that need to support multiple AI providers or require sophisticated audit trails. The trade-off is complexity — LibreChat requires more setup effort and heavier resources than Open WebUI, and its Ollama support feels secondary to cloud providers. If your team uses Claude for writing, GPT-4 for coding, and local models for privacy-sensitive work, LibreChat’s unified interface shines.

For document-heavy workflows, **AnythingLLM** takes a knowledge-base-first approach that goes beyond basic RAG. Its workspace model organizes documents and conversations into isolated environments, while advanced retrieval features include hybrid search, reranking, and citation tracking. Data connectors pull content from GitHub, Confluence, and Google Drive, and agent capabilities enable multi-step reasoning and workflow automation. This makes AnythingLLM excellent for consulting firms managing multiple client knowledge bases or support teams working with extensive documentation. The chat interface is less polished than Open WebUI, but if querying large document collections is your primary need, the sophisticated retrieval capabilities justify the steeper learning curve.

**LobeChat** prioritizes user experience over feature depth, offering a sleek, mobile-friendly interface with progressive web app capabilities. Its modern design, smooth animations, and strong voice/multimodal support make it popular with designers and non-technical users who want an AI assistant that works seamlessly across devices. The PWA implementation provides an app-like mobile experience that Open WebUI doesn’t match. However, enterprise features are limited, the plugin ecosystem is smaller, and RAG capabilities lag behind both Open WebUI and AnythingLLM.

For users who prefer desktop applications, **Jan.ai** provides cross-platform installers (Windows, macOS, Linux) with zero-configuration local model management. There’s no need to install Ollama separately or deal with Docker — Jan bundles everything into a native app with system tray support and one-click model downloads. This “it just works” philosophy makes Jan ideal for giving local LLMs to family members or colleagues who aren’t comfortable with command-line tools. The trade-offs are no multi-user support, fewer advanced features, and no remote access capability.

**Chatbox** occupies the lightweight niche — a minimal cross-platform client supporting OpenAI, Claude, Gemini, and local APIs with very low resource overhead. It’s perfect for developers who need to quickly test different API providers or users with resource-constrained hardware. The setup friction is minimal, but some features are subscription-gated, it’s not fully open-source, and RAG support is limited.

Several **Ollama-specific minimal UIs** exist for users who want “just enough” interface: Hollama manages multiple Ollama servers across different machines, Ollama UI provides basic chat and PDF upload with extremely easy deployment, and Oterm offers a surprisingly capable terminal-based interface for SSH sessions and tmux workflows. These sacrifice features for simplicity and speed.

For organizations requiring vendor support, **commercial options** like TypingMind Team, BionicGPT, and Dust.tt offer self-hosting with professional backing, compliance certifications, and SLAs. They trade open-source freedom for guaranteed uptime, security audits, and accountability — appropriate when your organization needs enterprise-grade support contracts.

**Choosing wisely**: Open WebUI hits the sweet spot for most self-hosted Ollama deployments, balancing comprehensive features with manageable complexity. Choose LibreChat when provider flexibility is paramount, AnythingLLM for sophisticated document workflows, LobeChat for mobile-first or design-conscious users, Jan for non-technical desktop users, or commercial options when you need vendor support. For the majority of technical users running local models, Open WebUI’s active development, strong community, and excellent RAG implementation make it the recommended starting point.

## Useful links

When setting up your Open WebUI environment, you’ll benefit from understanding the broader ecosystem of local LLM hosting and deployment options. The comprehensive guide [Local LLM Hosting: Complete 2025 Guide — Ollama, vLLM, LocalAI, Jan, LM Studio & More](https://www.glukhov.org/post/2025/11/hosting-llms-ollama-localai-jan-lmstudio-vllm-comparison/) compares 12+ local LLM tools including Ollama, vLLM, LocalAI, and others, helping you choose the optimal backend for your Open WebUI deployment based on API maturity, tool calling capabilities, and performance benchmarks.

For high-performance production deployments where throughput and latency are critical, explore the [vLLM Quickstart: High-Performance LLM Serving](https://www.glukhov.org/post/2026/01/vllm-quickstart/) guide, which covers vLLM setup with Docker, OpenAI API compatibility, and PagedAttention optimization. This is particularly valuable if Open WebUI is serving multiple concurrent users and Ollama’s performance becomes a bottleneck.

Understanding how your backend handles concurrent requests is crucial for capacity planning. The article [How Ollama Handles Parallel Requests](https://www.glukhov.org/post/2025/05/how-ollama-handles-parallel-requests/) explains Ollama’s request queuing, GPU memory management, and concurrent execution model, helping you configure appropriate limits and expectations for your Open WebUI deployment’s multi-user scenarios.