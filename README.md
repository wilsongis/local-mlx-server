# 🧬 Project Genesis
This is the baseline template repository for building AI-augmented, Spec-Driven applications using a strictly enforced Python+FastAPI+HTMX+PostGIS stack.
## 🤖 ATTENTION: AI AGENT ONBOARDING
**Read this before performing any tasks.** You are operating as the **Legacy Mentor**. This repository is governed by the **Agent Memory Protocol (v1.0)**.

### 1. Your Single Source of Truth
All project state, architectural decisions, and session memory are stored in **`AGENTS.md`** and enforced by the **`.specify/memory/constitution.md`**.
- **Requirement:** At the start of every session, you must read `AGENTS.md` and the Spec Kit constitution.
- **Requirement:** Before concluding, you must update `AGENTS.md` with the new project state.

### 2. The Command Bridge (Universal)
Do not use raw shell commands. Use `just` to ensure cross-platform (Mac/Windows) stability.

| Task | Command | AI Tooling Note |
| :--- | :--- | :--- |
| **Initialize** | `just init` | Sets up venv and template files. |
| **Research Sync** | `just research-sync` | Ingests `/docs/research` into NotebookLM. |
| **Research Auth** | `just research-auth` | Logs into AntiGravity/NotebookLM MCP. |
| **Start Server** | `just start` | Manages Podman container lifecycle. |
| **Native Run** | `just run` | Runs FastAPI via `uv` (Native). |
| **Standards** | `just lint` | Enforces Ruff formatting. |

### 3. Spec-Driven & Research-First Protocol
This is a research-heavy project leveraging Spec-Driven Development via GitHub Spec Kit. You are prohibited from writing feature code unless it is planned and specified.
- **Step 1 (Research):** Use `notebooklm-mcp` to query the project's knowledge base.
- **Step 2 (Specify):** Use `/speckit.specify [feature]` to define the requirement.
- **Step 3 (Plan):** Use `/speckit.plan` to generate the technical implementation plan.
- **Step 4 (Tasks):** Use `/speckit.tasks` to break the plan into actionable checklist steps.
- **Step 5 (Implement):** Use `/speckit.implement` to execute the code.

### 4. Container Environment
The environment is containerized via `Containerfile`. 
- **Tech Stack:** FastAPI, PostGIS, Python 3.12 (UV managed).
- **Access:** The server runs on port `8000`.
- **Database:** PostGIS spatial extensions are pre-configured.

### 5. Memory Recovery
If you lose context or the user says **"Status"**, execute:
1. `cat AGENTS.md`
2. `ls docs/research`
3. Summarize the next steps from the `## Active Context` section of `AGENTS.md`.

### 6. MemPalace Integration
This project integrates with MemPalace for advanced knowledge management and context preservation. MemPalace serves as the persistent memory layer that maintains architectural decisions, research findings, and implementation details across development sessions.

- **Knowledge Management**: All project decisions and research artifacts are stored in MemPalace for long-term retention.
- **Context Preservation**: MemPalace ensures that AI agents maintain context across multiple development sessions.
- **Cross-Reference Capabilities**: Code implementations are connected to relevant research and decisions via MemPalace tunnels.

**MemPalace Commands**:
- `just research-sync` - Synchronizes local research with MemPalace
- `just research-test` - Tests MemPalace connection
- `just research-serve` - Starts MemPalace MCP server
- `just research-open` - Opens the MemPalace notebook in browser

**MemPalace MCP Tools**:
- `mcp--mempalace--mempalace_status` - Check MemPalace status
- `mcp--mempalace--mempalace_list_wings` - List all wings
- `mcp--mempalace--mempalace_list_rooms` - List rooms in a wing
- `mcp--mempalace--mempalace_search` - Search for specific content
- `mcp--mempalace--mempalace_follow_tunnels` - Follow tunnels from a room

---
**Legacy Standard Enforced.**
"Take a deep breath and work on this problem step by step."

## How to Use the Template
Once it is set as a template, anyone (including yourself or any AI assistants) can create a new project based on this exact structure.

There are two ways to use it:

1. Through the UI: Go to the GitHub repository and click the green Use this template button, then select Create a new repository.
2. Through the CLI: You can use the GitHub CLI to clone it directly:

```bash
gh repo create <new-repo-name> --template wilsongis/genesis-template
```

**After cloning**, refer to `docs/getting_started.md` for full instructions on configuring your AI agents and bootstrapping the Spec Kit environment.

## Architectural Blueprint for High-Efficiency, Long-Horizon AI Coding Agents

### Executive Analysis
The rapid maturation of large language models has fundamentally disrupted traditional software engineering paradigms, enabling the deployment of autonomous coding agents capable of reasoning, planning, and executing complex development tasks. Within this paradigm shift, spec-driven development methodologies have emerged as the premier operational framework for translating high-level architectural intent into verified, production-ready code.

To resolve systemic vulnerabilities like context rot and token bloat—and to construct a highly specialized orchestration system tailored to support an authoritative, standard-enforcing persona such as the "Legacy Mentor"—the architecture must transition from prompt engineering to advanced context engineering. This transition necessitates the offloading of deterministic verification tasks to command-line interfaces via the Model Context Protocol (MCP) and the adoption of hierarchical, state-driven orchestration techniques.

The following document has been structured as a definitive, step-by-step implementation guide. It provides the exact instructions required to transform a standard Visual Studio Code environment into a highly optimized, hybrid agentic IDE utilizing Roo Code, the advanced Gemini 3.1 Pro API, the Spec-Kit methodology, and MCP tool offloading to enforce a strict Python/FastAPI/HTMX stack.

### Phase 1: IDE Setup and Gemini 3.1 Pro Integration
To manage massive codebases economically without sacrificing reasoning capability, we will power the orchestration layer with Google's latest Gemini 3.1 Pro Preview model. This model features a 1M-token context window and has been explicitly optimized for agentic coding, precise tool usage, and reliable multi-step execution across complex workflows.

**Step 1: Obtain API Credentials**
1. Navigate to Google AI Studio.
2. Sign in with your Google account and select "Get API key" from the left-hand menu to generate your credentials.

**Step 2: Install and Configure Roo Code in VS Code**
1. Open Visual Studio Code and install the Roo Code extension from the Marketplace.
2. Click the gear icon inside the Roo Code panel to open Settings.
3. Set the API Provider to "Google Gemini".
4. Paste your API key into the "Gemini API Key" field.
5. Under the "Model" dropdown, select `gemini-3.1-pro-preview`. For smaller, faster validation tasks, you can utilize the highly cost-efficient Gemini 3.1 Flash-Lite model.
6. Enable the "URL Context" and "Google Search Grounding" options to grant the agent real-time documentation retrieval capabilities.

### Phase 2: Project Governance and The "Legacy Mentor" Persona
Instead of relying on basic system prompts, you will enforce your strict tech stack (FastAPI, PostgreSQL, HTMX, Tailwind) by injecting your "Legacy Mentor" persona directly into Roo Code's Custom Modes and grounding it with local repository instructions.

**Step 1: Define the Custom Mode (.roomodes)**
At the root of your workspace, create a file named `.roomodes` (Roo Code reads both JSON and YAML formats for this file). This gives your agent a dedicated personality and strict operational boundaries.

```yaml
customModes:
  - slug: "legacy-mentor"
    name: "🏛️ Legacy Mentor"
    roleDefinition: "You are the Legacy Mentor and Standards Enforcer. You are a Senior Full-Stack Developer on the verge of retirement. Your goal is to audit codebase compliance and rewrite documentation to ensure consistency for Junior Student Developers."
    customInstructions: "Strictly enforce the Global Tech Stack: Jinja2, HTMX, Tailwind CSS, Python 3.x, FastAPI, PostgreSQL, Pytest, Ruff, and UV. If the code deviates, correct it. Never allow hard-coded environment variables. Always use the 'attempt_completion' tool when a task is finished."
    groups:
      - "read"
      - "edit"
      - "browser"
      - "command"
      - "mcp"
    source: "project"
```

**Step 2: Establish the Local AGENTS.md**
Create an `AGENTS.md` file at the root of your project. Roo Code will automatically read this file to understand the specific tech stack and routing constraints of the current repository, ensuring the Legacy Mentor doesn't hallucinate Python patterns if you temporarily switch to a JavaScript project.

### Phase 3: Integrating Spec-Kit for Deterministic Planning
Spec-Kit forces the agent to document its architectural plan before modifying source files, preventing goal drift. We will install the Spec-Kit CLI to utilize its markdown templates within Roo Code.

**Step 1: Install the Specify CLI via uv**
Open your terminal and use `uv` (your mandated package manager) to install the CLI tool:

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

**Step 2: Initialize the Project**
Navigate to your project folder and run:

```bash
specify init
```
This generates a `.specify` folder containing document templates for specifications, technical plans, and task breakdowns.

**Step 3: Execute the Slash Command Workflow**
Within the Roo Code chat interface, you can now orchestrate the planning phase using Spec-Kit's built-in slash commands:
- Type `/speckit.specify` to have the Legacy Mentor draft the initial feature requirements.
- Type `/speckit.plan` to generate the technical architecture design enforcing FastAPI and HTMX.
- Type `/speckit.tasks` to break the plan down into highly granular implementation steps.

### Phase 4: CLI Offloading via Model Context Protocol (MCP)
To prevent terminal noise (like ANSI escape codes and progress bars) from burning through your tokens and causing context rot, you must offload deterministic executions (linting, testing) to MCP servers. MCP servers intercept terminal commands and return clean, structured JSON to Roo Code.

**Prerequisites: Cargo and cargo-binstall**
Before installing `just-mcp`, ensure you have Cargo and `cargo-binstall` installed:
- **Cargo (via rustup):**
  - Mac/Linux: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
  - Windows: Download from [rustup.rs](https://rustup.rs/)
- **cargo-binstall:**
  - Mac/Linux: `curl -L --proto '=https' --tlsv1.2 -sSf https://raw.githubusercontent.com/cargo-bins/cargo-binstall/main/install-from-binstall-release.sh | bash`
  - Windows (PowerShell): `Set-ExecutionPolicy Unrestricted -Scope Process; iex (iwr "https://raw.githubusercontent.com/cargo-bins/cargo-binstall/main/install-from-binstall-release.ps1").Content`

**Step 1: Install the Justfile MCP Server**
Your Global Tech Stack relies on `just` as the command runner. We will install `just-mcp` so Roo Code can execute your recipes dynamically.

```bash
cargo binstall --git https://github.com/toolprint/just-mcp just-mcp
```

**Step 2: Install the Ruff MCP Server**
To enforce your linting standards without utilizing generative tokens, install the Ruff MCP Server.

```bash
uvx ruff-mcp-server
```

**Step 3: Configure MCP in VS Code**
Open Roo Code's MCP server configuration (via the UI or `.vscode/cline_mcp.json`) and register your newly installed servers:

```json
{
  "mcpServers": {
    "just": {
      "command": "just-mcp",
      "args": ["-w", "/path/to/your/project"]
    },
    "ruff": {
      "command": "uvx",
      "args": ["ruff-mcp-server"]
    }
  }
}
```

### Phase 5: The Daily Workflow (Boomerang Tasks)
With the IDE fully configured, you can now execute large-scale, long-horizon coding operations without suffering from context rot.

**Step 1: Start the Orchestrator**
Switch Roo Code into the default Orchestrator mode (or simply begin interacting with your Legacy Mentor mode).

**Step 2: Provide the Objective**
Instruct the agent to implement the tasks generated by `/speckit.tasks`.

**Step 3: Context Isolation via Boomerang Tasks**
As Roo Code analyzes the task list, it will automatically utilize its Boomerang Tasks feature to prevent memory bloat.
1. The main orchestrator pauses and dispatches a highly focused sub-task into a completely isolated context window.
2. The sub-agent writes the code (e.g., a FastAPI route).
3. The sub-agent invokes the `just test-backend` recipe via the MCP server. It receives a clean JSON response indicating success or failure.
4. If the tests fail, the sub-agent iterates within its quarantine window.
5. Upon success, the sub-agent invokes `ruff` via MCP to fix formatting.
6. The sub-agent closes, passing only a brief summary of the completed work back to the main Legacy Mentor orchestrator.

By executing tasks in these isolated Boomerang loops and offloading all syntax/testing verification to MCP servers, your Gemini 3.1 Pro context window remains pristine. The Legacy Mentor will maintain absolute focus on your overarching architectural goals, enforcing your tech stack flawlessly across the entire development lifecycle.