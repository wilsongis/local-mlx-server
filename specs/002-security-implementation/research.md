# Research: Security Implementation for Local MLX Inference Server

**Date**: 2026-05-05  
**Feature**: 002-security-implementation  
**Status**: Complete

## Research Questions & Findings

### 1. mlx_lm.server Security Configuration Options

**Decision**: Document mlx_lm.server's built-in security-related arguments and recommend configuration patterns.

**Rationale**: The server is the primary interface; understanding its native security controls (if any) is foundational.

**Findings**:
- `mlx_lm.server` provides OpenAI-compatible API with `--host` and `--port` arguments
- Default binding is localhost (127.0.0.1); network binding requires explicit `--host 0.0.0.0`
- No built-in authentication mechanism; relies on network-level controls
- No built-in rate limiting; requires external tooling or reverse proxy
- Input validation is handled by the server's request parsing (FastAPI/Starlette underlying)

**Alternatives considered**:
- Wrapping server with custom authentication middleware → Rejected: violates Infrastructure-Only Scope (Principle I)
- Using reverse proxy (nginx) for auth → Deferred: out of scope for local inference server

---

### 2. Path Traversal Prevention for Model Loading

**Decision**: Implement path validation using `os.path.realpath()` and prefix matching against authorized directories.

**Rationale**: Python's `os.path.realpath()` resolves symlinks and relative paths to absolute paths, enabling reliable prefix checks.

**Findings**:
- Use `pathlib.Path.resolve()` or `os.path.realpath()` to get canonical path
- Check if resolved path starts with authorized directory prefix
- Reject paths containing `..` early (defense in depth)
- Symlink targets must also be within authorized directories
- Log all path validation failures with sanitized paths (no full path logging)

**Best Practice**:
```python
from pathlib import Path

def validate_model_path(requested_path: str, authorized_dirs: list[str]) -> Path:
    resolved = Path(requested_path).resolve()
    for auth_dir in authorized_dirs:
        auth_resolved = Path(auth_dir).resolve()
        if str(resolved).startswith(str(auth_resolved)):
            return resolved
    raise SecurityError(f"Path {requested_path} not in authorized directories")
```

**Alternatives considered**:
- Chroot jailing → Not portable across macOS/Linux for this use case
- Restrictive file permissions only → Insufficient; path traversal can still occur

---

### 3. Environment Variable Security (Masking/Redaction)

**Decision**: Implement environment variable redaction in logging using a deny-list approach with pattern matching.

**Rationale**: Sensitive variables (API keys, tokens) must never appear in logs; pattern matching catches common naming conventions.

**Findings**:
- Define sensitive variable patterns: `*_KEY`, `*_TOKEN`, `*_SECRET`, `*_PASSWORD`, `API_KEY`, `AUTH_TOKEN`
- Use `logging.Filter` to redact sensitive values from log records
- Redact in both log output and error messages
- Process listings (`ps aux`) may still expose env vars—document as limitation
- `.env` file permissions should be `600` (owner read/write only)

**Implementation Approach**:
```python
import re
import os

SENSITIVE_PATTERNS = [r'.*_KEY$', r'.*_TOKEN$', r'.*_SECRET$', r'.*_PASSWORD$']

def is_sensitive_var(name: str) -> bool:
    return any(re.match(p, name) for p in SENSITIVE_PATTERNS)

def redact_env_vars(env_dict: dict) -> dict:
    return {k: '***REDACTED***' if is_sensitive_var(k) else v for k, v in env_dict.items()}
```

**Alternatives considered**:
- Not logging env vars at all → Too restrictive for debugging
- Allow-list approach → Incomplete; new sensitive vars could be missed

---

### 4. Rate Limiting for Local Inference Server

**Decision**: Document rate limiting recommendations; defer implementation to future specs (infrastructure-only scope).

**Rationale**: Rate limiting requires middleware or reverse proxy; documenting best practices fulfills the spec without violating scope.

**Findings**:
- For localhost-only: rate limiting less critical (single user)
- For network-accessible: recommend reverse proxy (nginx with `limit_req`)
- Token-based rate limiting more relevant than request-based for LLM inference
- `mlx_lm.server` has no built-in rate limiting

**Recommendation for Documentation**:
- Localhost default: No rate limiting required
- Network binding: Configure nginx `limit_req_zone` with appropriate burst values
- Future: Consider `slowapi` or similar FastAPI middleware if server code changes allowed

---

### 5. Fail-Closed Behavior for Security Controls

**Decision**: Document fail-closed as the default behavior; security control failures MUST block server startup or affected functionality.

**Rationale**: Fail-closed ensures security is never accidentally bypassed due to misconfiguration.

**Findings**:
- Path validation failure → Block model loading, log error, return 403 to API
- Environment variable validation failure → Block startup with clear error message
- Logging system failure exposing env vars → Block startup (fail-closed)
- Configuration file unreadable → Block startup with permission error

**Implementation Pattern**:
```python
def validate_security_config(config: dict) -> None:
    try:
        # Validate all security controls
        validate_paths(config['model_paths'])
        validate_env_vars(config['env'])
    except SecurityError as e:
        logger.critical(f"Security validation failed: {e}")
        sys.exit(1)  # Fail-closed: stop server
```

---

### 6. API Endpoint Security (OpenAI-Compatible Interface)

**Decision**: Document endpoint-specific security considerations; recommend disabling non-essential endpoints for attack surface reduction.

**Rationale**: The OpenAI-compatible API exposes multiple endpoints; disabling unused ones reduces attack surface.

**Findings**:
- Core endpoints (completions, chat): Always-on (FR-010)
- Non-essential endpoints: `/health`, `/metrics`, `/v1/models` (listing)
- Disable via configuration: Document `DISABLE_HEALTH_ENDPOINT=true` pattern
- Authentication: Document that localhost-only is default; network binding requires additional auth (reverse proxy)
- Input validation: `mlx_lm.server` uses Pydantic models; document validation behavior

**Endpoint Security Matrix**:

| Endpoint | Purpose | Default | Security Consideration |
|----------|---------|---------|------------------------|
| `/v1/chat/completions` | Chat inference | On | Core: always-on |
| `/v1/completions` | Text completion | On | Core: always-on |
| `/health` | Health check | On | Disable if not needed |
| `/metrics` | Prometheus metrics | On | Disable if not needed |
| `/v1/models` | List models | On | Disable to reduce info disclosure |

---

## Summary of Decisions

1. **Security boundaries**: Document localhost-only default; warn on network binding
2. **Path validation**: `Path.resolve()` + prefix matching against authorized dirs
3. **Env var redaction**: Deny-list patterns with `logging.Filter`
4. **Rate limiting**: Document only (reverse proxy recommendation)
5. **Fail-closed**: Block startup/functionality on security control failure
6. **Endpoint security**: Disable non-essential endpoints via configuration

All NEEDS CLARIFICATION resolved. Proceeding to Phase 1.
