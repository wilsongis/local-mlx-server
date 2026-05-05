# Data Model: Security Implementation for Local MLX Inference Server

**Date**: 2026-05-05  
**Feature**: 002-security-implementation  
**Status**: Complete

## Entities

### 1. Security Boundary

Defines network-level constraints for server exposure.

| Field | Type | Required | Validation | Description |
|-------|------|----------|-------------|-------------|
| `bind_host` | string | Yes | Must be valid IP or hostname | Network interface to bind (default: `127.0.0.1`) |
| `bind_port` | integer | Yes | 1024-65535 | Port for server listening |
| `allow_network` | boolean | No | Default: `false` | Whether to allow non-localhost binding |
| `network_warning` | string | No | N/A | Warning message when network binding enabled |

**State Transitions**:
```
[INITIAL] → bind_host=127.0.0.1, allow_network=false
   ↓ (user configures allow_network=true)
[NETWORK_ENABLED] → bind_host can be set to 0.0.0.0 or specific IP
```

**Validation Rules**:
- If `allow_network=true`, log security warning
- `bind_host` must be valid IP address (use `ipaddress` module)
- Default (`127.0.0.1`) requires no additional validation

---

### 2. API Endpoint

Represents an OpenAI-compatible API endpoint exposed by `mlx_lm.server`.

| Field | Type | Required | Validation | Description |
|-------|------|----------|-------------|-------------|
| `path` | string | Yes | Must start with `/` | Endpoint URL path |
| `method` | string | Yes | One of: GET, POST | HTTP method |
| `is_core` | boolean | Yes | N/A | Whether endpoint is core inference (always-on) |
| `is_enabled` | boolean | No | Default: `true` | Whether endpoint is currently enabled |
| `rate_limit` | string | No | Format: "N/period" | Rate limit (e.g., "100/minute") |

**Core Endpoints** (always-on, `is_core=true`):
- `/v1/chat/completions` (POST)
- `/v1/completions` (POST)

**Non-Essential Endpoints** (can be disabled):
- `/health` (GET) → `is_core=false`
- `/metrics` (GET) → `is_core=false`
- `/v1/models` (GET) → `is_core=false`

**Validation Rules**:
- Core endpoints cannot be disabled (enforce `is_enabled=true` if `is_core=true`)
- Non-essential endpoints can be disabled via configuration
- Rate limiting applies only if `is_enabled=true`

---

### 3. Model Path

Filesystem location for model files with authorization constraints.

| Field | Type | Required | Validation | Description |
|-------|------|----------|-------------|-------------|
| `original_path` | string | Yes | N/A | User-provided path (may be relative/symlink) |
| `resolved_path` | string | Yes | Must exist, must be absolute | Canonical absolute path after resolution |
| `is_authorized` | boolean | Yes | N/A | Whether path passes security validation |
| `authorization_source` | string | Yes | One of: configured, default | Which authorized dir granted access |

**Validation Rules**:
- `resolved_path` must start with one of the configured authorized directories
- Symlink targets must also be within authorized directories
- Path traversal sequences (`..`) rejected before resolution
- Non-existent paths: reject with 404 (not 403, to avoid info disclosure)

**Security Flow**:
```
User provides path → Check for .. → Resolve symlinks → Prefix match against authorized dirs → Accept/Reject
```

---

### 4. Environment Variable

Configuration value passed to server process, categorized by sensitivity.

| Field | Type | Required | Validation | Description |
|-------|------|----------|-------------|-------------|
| `name` | string | Yes | Regex: `^[A-Za-z_][A-Za-z0-9_]*$` | Variable name |
| `value` | string | Yes | N/A | Variable value |
| `is_sensitive` | boolean | Yes | N/A | Whether variable contains sensitive data |
| `redacted_value` | string | No | Always `***REDACTED***` | Value for logging |
| `source` | string | No | One of: env, .env, default | Where variable was loaded from |

**Sensitive Patterns** (set `is_sensitive=true`):
- `*_KEY` (e.g., `OPENAI_API_KEY`)
- `*_TOKEN` (e.g., `AUTH_TOKEN`)
- `*_SECRET` (e.g., `JWT_SECRET`)
- `*_PASSWORD` (e.g., `DB_PASSWORD`)
- `API_KEY`
- `AUTH_TOKEN`

**Validation Rules**:
- Sensitive variables: never log `value`; always use `redacted_value`
- `.env` file permissions should be `600` (owner read/write only)
- On validation failure: fail-closed (block startup)

---

## Relationships

```
SecurityBoundary (1) ──── controls ──── (many) APIEndpoint
AuthorizedDirectory (many) ──── authorize ──── (many) ModelPath
EnvironmentVariable (many) ──── configure ──── SecurityBoundary
EnvironmentVariable (many) ──── configure ──── APIEndpoint
```

## Validation Summary

| Entity | Key Validation | Failure Behavior |
|--------|---------------|------------------|
| SecurityBoundary | Valid IP, localhost default | Fail-closed: block startup |
| APIEndpoint | Core cannot be disabled | Log warning, enforce always-on |
| ModelPath | Prefix match, no traversal | Return 403/404, log violation |
| EnvironmentVariable | Sensitive redaction | Fail-closed: block startup |
