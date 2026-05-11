# Data Model: Operations Runbook

**Feature**: 003-operations-runbook  
**Date**: 2026-05-07  
**Status**: Complete

## Overview

This feature is documentation-only and does not introduce traditional data models (no database schemas or code entities). However, it defines structured documentation entities that organize the operations runbook content in OPERATIONS.md.

## Documentation Entities

### 1. Just Recipe

**Description**: Operational command exposed through the `just` command bridge.

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Recipe name (kebab-case) |
| `description` | string | Yes | Brief description of functionality |
| `syntax` | string | Yes | Command syntax with arguments |
| `arguments` | array | No | List of arguments with defaults and descriptions |
| `examples` | array | Yes | Working examples with expected output |
| `edge_cases` | array | Yes | Error conditions and recovery steps |
| `developer_notes` | string | No | Guidelines for contributors adding/modifying recipes |

**Relationships**:
- Referenced by Troubleshooting Scenario (when recipe usage fails)
- Referenced by Model Profile (recipes may invoke specific profiles)

**Validation Rules**:
- Name must follow kebab-case convention
- At least one working example must be provided
- Edge cases must cover invalid arguments and error conditions
- Must match authoritative definition in [justfile](../justfile)

---

### 2. Troubleshooting Scenario

**Description**: Structured guide for resolving common operational issues.

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `issue_type` | enum | Yes | Category: startup, memory, network, model-load, other |
| `symptoms` | array | Yes | Observable error messages or behaviors |
| `root_cause` | string | Yes | Underlying technical cause |
| `resolution_steps` | array | Yes | Ordered list of remediation actions |
| `prevention_tips` | array | No | Best practices to avoid recurrence |
| `related_recipes` | array | No | `just` recipes that can help diagnose/resolve |

**State Transitions**:
```
[Detected] → [Diagnosed] → [Resolved]
     ↓
[Escalated] (if resolution fails)
```

**Validation Rules**:
- Must cover at least 5 startup scenarios (FR-004)
- Must cover at least 3 memory-related issues (FR-005)
- Resolution steps must be ordered and testable
- Root cause must reference Apple Silicon / MLX specifics

---

### 3. Model Profile

**Description**: Memory-tier configuration for optimizing 120B+ model serving.

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `memory_tier` | enum | Yes | 48GB, 64GB, or 96GB |
| `profile_name` | string | Yes | Human-readable profile identifier |
| `quantization_config` | object | Yes | Weight compression and KV cache settings |
| `performance_metrics` | object | Yes | tok/s, context length, memory used |
| `compatibility` | array | Yes | Supported model architectures |
| `fallback_rule` | string | No | Rule for between-tier systems |

**Performance Metrics Sub-object**:
| Field | Type | Example |
|-------|------|---------|
| `tokens_per_second` | float | 15.0 |
| `context_length` | integer | 2048 |
| `memory_used_gb` | float | 42.0 |

**Validation Rules**:
- Must define all three tiers: 48GB, 64GB, 96GB (FR-006)
- Must include quantifiable metrics per FR-007
- Fallback rule must enforce lower-tier preference for between-tier systems (FR-011)
- Must align with TurboQuant hybrid quantization research

---

## Decision Tree Entity (Special)

### Model Profile Selection Decision Tree

**Description**: Flowchart for operators to select correct profile based on system memory.

**Nodes**:
1. **Start**: Check system memory
   - Command: `system_profiler SPHardwareDataType | grep Memory` or `sysctl hw.memsize`
   
2. **Decision**: Memory < 64GB?
   - Yes → 48GB Profile (15 tok/s, 2K context, 42GB used)
   - No → Continue
   
3. **Decision**: Memory < 96GB?
   - Yes → 64GB Profile (22 tok/s, 4K context, 56GB used)
   - No → 96GB Profile (30 tok/s, 8K context, 80GB used)
   
4. **Edge Case**: Memory between tiers (e.g., 56GB)?
   - Apply fallback rule: Use lower tier (48GB Profile)
   - Rationale: Stability over performance

**Validation Rules**:
- 100% accuracy for edge cases including between-tier systems (SC-007)
- Must use lower-tier fallback rule (FR-011)
- Must provide commands to check system memory (FR-006)

---

## Entity Relationships

```text
Just Recipe ←→ Troubleshooting Scenario
    ↓                    ↑
    └────────────────────┘
         (recipes help
          resolve issues)

Model Profile ←→ Just Recipe
    ↓              ↑
    └──────────────┘
    (recipes invoke
     specific profiles)

Troubleshooting Scenario ←→ Model Profile
    ↓                         ↑
    └─────────────────────────┘
    (memory issues may require
     profile adjustment)
```

---

## Documentation Structure in OPERATIONS.md

Based on the entities above, the updated OPERATIONS.md will be structured as:

```text
OPERATIONS.md
├── Just Recipe Reference
│   ├── Recipe 1: start-server
│   ├── Recipe 2: stop-server
│   ├── ...
│   └── Developer Guidelines (contribution standards)
├── Troubleshooting Guide
│   ├── Startup Failures (5+ scenarios)
│   ├── Memory Issues (3+ scenarios)
│   └── Diagnostic Commands
├── Model Profile Decision Tree
│   ├── 48GB Tier (metrics + config)
│   ├── 64GB Tier (metrics + config)
│   ├── 96GB Tier (metrics + config)
│   └── Decision Flowchart
└── Appendix
    ├── Quick Reference
    └── Related Documentation
```

---

## Validation Checklist

- [ ] All `just` recipes in justfile documented (FR-001)
- [ ] At least one working example per recipe (FR-002)
- [ ] Edge cases documented per recipe (FR-003)
- [ ] 5+ startup failure scenarios (FR-004)
- [ ] 3+ memory-related issues (FR-005)
- [ ] 48GB/64GB/96GB tiers mapped (FR-006)
- [ ] Quantifiable metrics per tier (FR-007)
- [ ] Lower-tier fallback rule documented (FR-011)
- [ ] "just recipe" terminology used consistently (FR-009)
- [ ] Infrastructure-only scope maintained (FR-008)
