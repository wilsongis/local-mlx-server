# API Endpoint Contracts: Security Implementation

**Date**: 2026-05-05  
**Feature**: 002-security-implementation  
**Status**: Complete

## Contract Format

For the local MLX inference server (OpenAI-compatible), the contract defines:
- Endpoint path and method
- Security requirements
- Input validation rules
- Expected behavior when security controls are active

---

## Core Endpoints (Always-On)

### 1. Chat Completions

**Endpoint**: `POST /v1/chat/completions`

**Security Requirements**:
- Always enabled (core inference endpoint)
- If authentication configured: require valid API key in `Authorization` header
- Input validation: `mlx_lm.server` uses Pydantic models (FastAPI underlying)

**Request Contract**:
```json
{
  "model": "string (required, validated against available models)",
  "messages": "array of objects (required, validated for content safety)",
  "temperature": "float (optional, 0.0-2.0)",
  "max_tokens": "integer (optional, positive)",
  "stream": "boolean (optional, default false)"
}
```

**Security Notes**:
- No rate limiting built-in; document reverse proxy recommendation
- Input size limits: document maximum request size (prevent DoS)
- Response may contain sensitive generated content; document access controls

---

### 2. Text Completions

**Endpoint**: `POST /v1/completions`

**Security Requirements**:
- Always enabled (core inference endpoint)
- Same security profile as chat completions

**Request Contract**:
```json
{
  "model": "string (required)",
  "prompt": "string (required, validated for content safety)",
  "temperature": "float (optional)",
  "max_tokens": "integer (optional)"
}
```

---

## Non-Essential Endpoints (Can Be Disabled)

### 3. Health Check

**Endpoint**: `GET /health`

**Security Requirements**:
- Can be disabled via configuration (`DISABLE_HEALTH_ENDPOINT=true`)
- No authentication required (information disclosure risk)
- Recommended: disable if not monitoring

**Response Contract**:
```json
{
  "status": "string (ok/degraded/error)",
  "model_loaded": "boolean",
  "timestamp": "ISO 8601 timestamp"
}
```

**Security Risk**: Information disclosure (server status, model availability)

---

### 4. Metrics

**Endpoint**: `GET /metrics`

**Security Requirements**:
- Can be disabled via configuration (`DISABLE_METRICS_ENDPOINT=true`)
- No authentication (Prometheus scraping assumes trusted network)
- Recommended: disable if not using Prometheus

**Response Contract**:
```
# Prometheus text format
mlx_inference_requests_total{endpoint="/v1/chat/completions"} 42
mlx_inference_latency_seconds{quantile="0.95"} 1.234
```

**Security Risk**: Operational intelligence disclosure

---

### 5. List Models

**Endpoint**: `GET /v1/models`

**Security Requirements**:
- Can be disabled via configuration (`DISABLE_MODELS_ENDPOINT=true`)
- No authentication required
- Recommended: disable to reduce attack surface

**Response Contract**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "model-name",
      "object": "model",
      "created": 1234567890,
      "owned_by": "local"
    }
  ]
}
```

**Security Risk**: Model enumeration (reveals available models)

---

## Security Configuration Contract

### Environment Variables (`.env`)

```bash
# Network Security
MLX_HOST=127.0.0.1                    # Default: localhost-only
MLX_PORT=8000                          # Default: 8000
ALLOW_NETWORK_BINDING=false            # Set true to allow 0.0.0.0 binding

# Endpoint Security
DISABLE_HEALTH_ENDPOINT=false          # Set true to disable /health
DISABLE_METRICS_ENDPOINT=false         # Set true to disable /metrics
DISABLE_MODELS_ENDPOINT=false          # Set true to disable /v1/models

# Path Security
AUTHORIZED_MODEL_DIRS=/path/to/models  # Colon-separated on Linux, semicolon on Windows

# Environment Variable Security
REDACT_SENSITIVE_VARS=true             # Redact *_KEY, *_TOKEN in logs
```

### Fail-Closed Behavior

| Condition | Behavior |
|-----------|----------|
| Invalid model path | Return 403, log security violation, do not load model |
| Unauthorized model dir | Return 403, log attempt, do not load model |
| Sensitive var in log | Redact value, log warning about exposure attempt |
| Config file unreadable | Block server startup with permission error |
| Network bind + ALLOW_NETWORK_BINDING=false | Block startup with clear error |

---

## Input Validation Rules

### Request Size Limits
- Document maximum request size (prevent buffer overflow / DoS)
- Recommend reverse proxy with `client_max_body_size` (nginx)

### Content Safety
- `mlx_lm.server` validates request format via Pydantic
- No content filtering built-in (document as limitation)
- Malformed requests: return 422 Unprocessable Entity

### Input Validation Contract (FR-003)

#### Request Body Schema Validation
- **Content-Type**: Must be `application/json` (reject others with 415 Unsupported Media Type)
- **JSON Structure**: Valid JSON object with required fields per endpoint
- **Field Types**: Validate string, number, boolean types per Pydantic schema

#### String Length Limits
- **Prompt/Message Content**: Maximum 4096 characters per prompt/message
- **Model Name**: Maximum 256 characters
- **Exceeds limit**: Return 400 Bad Request with error message

#### Prohibited Character Sequences
- **Path Traversal**: Reject inputs containing `../` or `..\\` patterns
- **Shell Metacharacters**: Reject inputs with `` ` ``, `$()`, `${}`, `|`, `;`, `&&`, `||`
- **Detection**: Apply to all string fields (prompt, messages, model name)
- **Violation Response**: Return 400 Bad Request with "Invalid input detected"

#### Content-Type Validation
- **Required**: `Content-Type: application/json`
- **Empty body**: Reject with 400 Bad Request
- **Wrong content-type**: Reject with 415 Unsupported Media Type
- **Missing content-type**: Treat as 415 Unsupported Media Type

### Path Traversal Prevention
- All model paths validated against `AUTHORIZED_MODEL_DIRS`
- Resolution: `Path(requested_path).resolve()` before check
- Reject if resolved path doesn't start with authorized prefix

---

## Security Headers (Recommended)

When using reverse proxy:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Content-Security-Policy: default-src 'none'
```

---

## Contract Validation

To validate this contract:
1. Start server with `just run`
2. Test each endpoint with/without authentication
3. Test path traversal attempts against model loading
4. Verify environment variable redaction in logs
5. Test disabling non-essential endpoints
6. Test input validation (malformed JSON, oversized prompts, path traversal in inputs, wrong content-type)
