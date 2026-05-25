# Data Model: Startup Preflight and Degraded Mode

**Feature**: 010-offline-002-startup | **Date**: 2026-05-24

## Entities

### PreflightCheck

Represents a single validation step in the preflight process.

**Fields**:
- `name: str` - Unique identifier for the check (e.g., "memory_budget", "wired_limit")
- `check_type: str` - Category: "critical" or "non_critical"
- `status: str` - Result: "pass", "fail", "warning", "skip"
- `details: str` - Human-readable description of the result
- `timestamp: datetime` - When the check was executed
- `error_code: Optional[str]` - Error code if check failed (e.g., "ERR-MEM-001")

**Validation Rules**:
- `name` must be unique within a preflight run
- `check_type` must be either "critical" or "non_critical"
- `status` must be one of: "pass", "fail", "warning", "skip"

**State Transitions**:
```
[initialized] → [running] → [pass | fail | warning | skip]
```

---

### PreflightResult

Aggregated result of all preflight checks with the final decision.

**Fields**:
- `checks: List[PreflightCheck]` - All individual check results
- `overall_status: str` - "ready", "degraded", "blocked"
- `critical_failures: List[str]` - Names of failed critical checks
- `non_critical_failures: List[str]` - Names of failed non-critical checks
- `degraded_mode: bool` - Whether system should enter degraded mode
- `block_startup: bool` - Whether startup should be blocked
- `execution_time_ms: int` - Total preflight execution time

**Validation Rules**:
- If any critical check fails → `block_startup = True`, `overall_status = "blocked"`
- If non-critical checks fail but all critical pass → `degraded_mode = True`, `overall_status = "degraded"`
- If all checks pass → `overall_status = "ready"`

**Decision Logic**:
```python
if any(c.check_type == "critical" and c.status == "fail" for c in checks):
    overall_status = "blocked"
    block_startup = True
elif any(c.status == "fail" for c in checks):
    overall_status = "degraded"
    degraded_mode = True
else:
    overall_status = "ready"
```

---

### DegradedModeConfig

Configuration for operating in degraded mode with reduced capabilities.

**Fields**:
- `enabled: bool` - Whether degraded mode is active
- `disabled_features: List[str]` - Features to disable (e.g., "turboquant", "kv_cache_compression")
- `fallback_quantization: str` - Quantization to use (e.g., "4bit-standard")
- `fallback_profile: str` - Profile name to use in degraded mode
- `warnings: List[str]` - User-facing warning messages

**Default Disabled Features** (from FR-007):
1. TurboQuant hybrid quantization
2. KV cache compression
3. Advanced profiling tools

**Validation Rules**:
- `fallback_quantization` must be a valid preset in `scripts/wrapper-config/presets.yaml`
- `disabled_features` must only contain known feature names

---

### StartupAttempt

Record of a server start attempt for logging and diagnostics.

**Fields**:
- `timestamp: datetime` - When the start was attempted
- `preflight_result: PreflightResult` - The preflight check results
- `startup_status: str` - "success", "failed", "degraded"
- `error_details: Optional[str]` - Error message if startup failed
- `model_path: str` - Path to the model being loaded
- `profile_used: str` - Quantization profile that was selected

**State Transitions**:
```
[attempt] → [preflight_running] → [preflight_passed | preflight_failed]
preflight_passed → [server_starting] → [success | degraded]
preflight_failed → [blocked]
```

---

## Relationships

```
StartupAttempt (1) → (1) PreflightResult
PreflightResult (1) → (many) PreflightCheck
PreflightResult (1) → (1) DegradedModeConfig (optional, only if degraded)
```

---

## Model Size Class Thresholds

From `scripts/quantization/kv_cache_profiles.py` (lines 11-37):

| Class | Memory Min (GB) | Weight Bits | KV Bits | Profile Example |
|-------|------------------|-------------|---------|-----------------|
| 20B | 32 | 3 | 4 | Balanced for smaller models |
| 70B | 32 | 3 | 3 | Mid-size optimization |
| 100B+ | 48 | 3 | 3 | TurboQuant hybrid (FR-002) |

---

## Health Endpoint Extensions

The existing `mlx_lm.server` health endpoint will be extended with:

```json
{
  "status": "healthy|degraded|blocked",
  "preflight": {
    "last_check": "2026-05-24T18:00:00Z",
    "overall_status": "ready|degraded|blocked",
    "checks": [
      {"name": "memory_budget", "status": "pass", "type": "critical"}
    ]
  },
  "degraded_mode": {
    "active": false,
    "disabled_features": [],
    "fallback_profile": null
  }
}
```
