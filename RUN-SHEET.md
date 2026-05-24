# RUN SHEET: First 2 Weeks Execution Plan

This run sheet converts the prioritized recommendations into a copy-paste workflow.

All work follows the required command chain:

1. `/speckit.specify`
2. `/speckit.plan`
3. `/speckit.tasks`
4. `/speckit.implement`
5. `/speckit.verify`

Use this exactly in order for each item below.

---

## Ranked Order (First 2 Weeks)

1. **ADMIN-001: Admin GUI MVP for immediate server visibility and control**
2. OFFLINE-002: Startup preflight and degraded-mode
3. QUANT-006: KV compatibility hardening
4. QUANT-005: Runtime quantization policy engine
5. DEPS-003: Offline dependency bundle
6. OFFLINE-001: Offline model artifact mirror
7. OBS-003: Offline incident telemetry
8. OFFLINE-003: Local runbook snapshot and restore
9. FUTURE-004: Incremental KV dequantization spike
10. FUTURE-005: Embedding quantization spike
11. FUTURE-006: External quantizer parity benchmark spike

---

## Immediate / Day 0: ADMIN-001 (Admin GUI MVP)

Get a working web interface immediately for server visibility and basic control. Per project governance, the web UI lives in a separate directory and calls `just` commands.

### ADMIN-001: Admin GUI MVP

#### ADMIN-001 commands

```text
/speckit.specify "ADMIN-001 Admin GUI MVP with just command integration for immediate server visibility and control"
/speckit.plan "Create separate admin-gui directory with lightweight web UI that calls just commands for: server status, model status, start/stop controls, and health display"
/speckit.tasks "Create tasks for admin-gui scaffold, just command bridge, server status view, model view, and basic controls"
/speckit.implement "Execute all tasks for ADMIN-001 with focus on immediate usability"
/speckit.verify "Acceptance: working web UI at localhost:3000 showing server status, active model, and start/stop controls via just bridge"
```

#### ADMIN-001 acceptance criteria

- [ ] Separate `admin-gui/` directory with standalone web application.
- [ ] Web UI calls `just` commands via backend bridge (not direct server imports).
- [ ] Server status dashboard shows: running state, active model, uptime, memory usage.
- [ ] Model management view shows: available models, active model, quantization profiles.
- [ ] Basic controls: start server, stop server, restart server via `just` recipes.
- [ ] Health display shows: last health check result, endpoint responsiveness.
- [ ] UI is accessible at `localhost:3000` after `just admin-gui` recipe.
- [ ] `just admin-gui` recipe added to justfile for starting the GUI.

---

## Week 1

### Day 1-2: OFFLINE-002

#### OFFLINE-002 commands

```text
/speckit.specify "OFFLINE-002 Startup Preflight and Degraded Mode for Apple Silicon local serving"
/speckit.plan "Implement preflight checks for memory budget, wired-limit, disk space, dependency integrity, and deterministic profile fallback"
/speckit.tasks "Create dependency-ordered tasks including just preflight and just preflight-offline"
/speckit.implement "Execute all tasks for OFFLINE-002"
/speckit.verify "Acceptance: preflight detects unsafe profile, auto-falls back deterministically, and offline preflight returns actionable remediation"
```

#### OFFLINE-002 acceptance criteria

- [ ] Preflight checks memory budget, wired-limit constraints, disk headroom, and dependency integrity.
- [ ] Deterministic fallback selects the next safe profile when target profile is unsafe.
- [ ] `just preflight` and `just preflight-offline` provide pass/fail and remediation messages.

---

### Day 2-3: QUANT-006

#### QUANT-006 commands

```text
/speckit.specify "QUANT-006 KV Compatibility Hardening for Hybrid Attention and Attention Sinks"
/speckit.plan "Harden prompt-first conversion and fallback behavior for incompatible quantized SDPA paths"
/speckit.tasks "Create tests/tasks for KVCache, RotatingKVCache, ArraysCache, and attention sink compatibility"
/speckit.implement "Execute all tasks for QUANT-006"
/speckit.verify "Acceptance: no crash on sink/hybrid paths, prompt-first conversion validated, and safe fallback path is explicit"
```

#### QUANT-006 acceptance criteria

- [ ] Prompt-first cache conversion is validated before generation starts.
- [ ] KVCache, RotatingKVCache, and ArraysCache paths are handled explicitly.
- [ ] Attention sink scenarios do not crash.
- [ ] Incompatible quantized SDPA routes fall back to a safe path.

---

### Day 3-4: QUANT-005

#### QUANT-005 commands

```text
/speckit.specify "QUANT-005 Runtime Quantization Policy Engine for Prompt-Aware and Model-Scale Defaults"
/speckit.plan "Implement prompt-aware sampler rules, model-scale KV policy, and min_tokens safety for think-enabled models"
/speckit.tasks "Generate tasks covering policy config, enforcement hooks, and regression tests"
/speckit.implement "Execute all tasks for QUANT-005"
/speckit.verify "Acceptance: numeric prompts disable repetition penalty, KV defaults enforced by model scale, premature EOS prevented via min_tokens policy"
```

#### QUANT-005 acceptance criteria

- [ ] Numeric prompts disable repetition penalty policy path.
- [ ] KV bit policy is enforced by model scale.
- [ ] Think-enabled profiles enforce safe `min_tokens` defaults.

---

### Day 4-5: DEPS-003

#### DEPS-003 commands

```text
/speckit.specify "DEPS-003 Offline Dependency Bundle and Air-Gapped Install Workflow"
/speckit.plan "Build reproducible wheelhouse workflow with lock/manifests and network-disabled validation"
/speckit.tasks "Create tasks for just deps-bundle, just deps-install-offline, checksum manifesting, and clean-host verification"
/speckit.implement "Execute all tasks for DEPS-003"
/speckit.verify "Acceptance: clean Apple Silicon host installs fully offline from bundle with deterministic dependency resolution"
```

#### DEPS-003 acceptance criteria

- [ ] Offline bundle includes lock file, wheelhouse, and checksummed manifest.
- [ ] `just deps-bundle` and `just deps-install-offline` are implemented.
- [ ] Clean-host install works with network disabled.

---

## Week 2

### Day 1-2: OFFLINE-001

#### OFFLINE-001 commands

```text
/speckit.specify "OFFLINE-001 Local Model Artifact Mirror with Integrity Verification"
/speckit.plan "Define mirror layout and checksum verification for weights, tokenizer assets, and model card metadata"
/speckit.tasks "Create tasks for just models-mirror and just models-verify plus cold-start no-network validation"
/speckit.implement "Execute all tasks for OFFLINE-001"
/speckit.verify "Acceptance: mirrored artifacts pass checksum verification and server cold-start works with internet disconnected"
```

#### OFFLINE-001 acceptance criteria

- [ ] Local mirror layout is documented and implemented.
- [ ] Weights, tokenizer assets, and metadata are covered by checksums.
- [ ] Offline cold-start succeeds with no internet access.

---

### Day 2-3: OBS-003

#### OBS-003 commands

```text
/speckit.specify "OBS-003 Offline Incident Telemetry and Triage Reporting"
/speckit.plan "Capture structured local incidents and rolling benchmark deltas with offline triage commands"
/speckit.tasks "Create tasks for just incidents-tail and just incidents-report plus event schema and retention policy"
/speckit.implement "Execute all tasks for OBS-003"
/speckit.verify "Acceptance: OOM/wired-limit/kernel failures are logged with profile context and report output supports offline triage"
```

#### OBS-003 acceptance criteria

- [ ] Structured incident logs exist for OOM, wired-limit, and kernel failures.
- [ ] Per-profile rolling deltas track tokens/sec, peak memory, and quality checks.
- [ ] `just incidents-tail` and `just incidents-report` support offline triage.

---

### Day 3-4: OFFLINE-003

#### OFFLINE-003 commands

```text
/speckit.specify "OFFLINE-003 Last-Known-Good Runbook Snapshot and Restore"
/speckit.plan "Implement snapshot/restore of profile, sampler, cache bits, context defaults, and failure fingerprints"
/speckit.tasks "Create tasks for just runbook-snapshot and just runbook-restore with recovery validation"
/speckit.implement "Execute all tasks for OFFLINE-003"
/speckit.verify "Acceptance: one-command restore rehydrates known-good runtime and includes remediation hints by failure fingerprint"
```

#### OFFLINE-003 acceptance criteria

- [ ] Last-known-good runtime settings are persisted.
- [ ] `just runbook-snapshot` and `just runbook-restore` are implemented.
- [ ] Restore workflow recovers service configuration with remediation hints.

---

### Day 4-5: Future Spikes (Timeboxed)

#### FUTURE-004

```text
/speckit.specify "FUTURE-004 Incremental KV Dequantization Spike for Large-Context Throughput"
/speckit.plan "Prototype dequantization of appended segments only with low-memory fallback to full-step path"
/speckit.tasks "Create spike tasks and benchmark matrix for 20B, 32B, 120B, 122B"
/speckit.implement "Execute all spike tasks for FUTURE-004"
/speckit.verify "Acceptance: benchmark report produced and fallback behavior proven under constrained memory"
```

Acceptance criteria:

- [ ] Prototype demonstrates incremental dequantization behavior.
- [ ] Benchmark report covers 20B, 32B, 120B, 122B.
- [ ] Low-memory fallback path is tested.

#### FUTURE-005

```text
/speckit.specify "FUTURE-005 Embedding and Output Layer Quantization Spike with Quality Guardrails"
/speckit.plan "Prototype embedding quantization path with opt-out switch and small-model quality checks"
/speckit.tasks "Create spike tasks for 1B-7B size-quality analysis and instruction-following regression checks"
/speckit.implement "Execute all spike tasks for FUTURE-005"
/speckit.verify "Acceptance: report documents size gains, quality impact, and guardrail thresholds for rollout/no-rollout"
```

Acceptance criteria:

- [ ] Embedding quantization path exists with opt-out.
- [ ] 1B-7B report includes size and quality impact.
- [ ] Guardrail threshold is defined for go/no-go.

#### FUTURE-006

```text
/speckit.specify "FUTURE-006 External Quantizer Parity Benchmark Framework (TurboQuant vs GPTQ vs AWQ)"
/speckit.plan "Design reproducible benchmark framework with identical prompts, contexts, and reporting schema"
/speckit.tasks "Create spike tasks for harness, config manifests, metric collection, and publishable result template"
/speckit.implement "Execute all spike tasks for FUTURE-006"
/speckit.verify "Acceptance: reproducible parity report generated with quality, speed, memory, and operational complexity comparisons"
```

Acceptance criteria:

- [ ] Identical prompt/context benchmark harness across TurboQuant, GPTQ, and AWQ.
- [ ] Reproducible report includes quality, speed, memory, and operational complexity.
- [ ] Config manifests are versioned for repeat runs.

---

## Completion Gate (Run after each item)

```text
/speckit.verify "Confirm acceptance criteria met, update completed tasks, and attach evidence links"
```

Exit criteria per item:

- [ ] Acceptance criteria boxes are complete.
- [ ] Evidence exists (tests, benchmark outputs, logs, command transcripts).
- [ ] Rollback notes are recorded in spec quickstart or operations docs.
