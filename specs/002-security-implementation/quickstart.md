# Quickstart: Security Implementation for Local MLX Inference Server

**Date**: 2026-05-05  
**Feature**: 002-security-implementation  
**Status**: Complete

## Prerequisites

- Local MLX server operational (see `just run` in [OPERATIONS.md](OPERATIONS.md))
- `.env` file configured (copy from `.env.example`)
- Python 3.11+ with `mlx-lm` installed

---

## Step 1: Secure Network Binding (Default: Localhost-Only)

**Goal**: Ensure server only binds to localhost by default.

### Check Current Configuration

```bash
# View current host binding
grep MLX_HOST .env || echo "MLX_HOST not set (default: 127.0.0.1)"
```

### Set Secure Default

```bash
# Add to .env (if not present)
echo "MLX_HOST=127.0.0.1" >> .env
echo "ALLOW_NETWORK_BINDING=false" >> .env
```

### Verify

```bash
# Start server and verify binding
just run
# Should see: "Running on http://127.0.0.1:8000"
```

⚠️ **Warning**: Never set `MLX_HOST=0.0.0.0` unless you understand the security implications. If you must bind to network:
1. Set `ALLOW_NETWORK_BINDING=true`
2. Configure firewall rules
3. Use reverse proxy with authentication

---

## Step 2: Restrict Model Loading to Authorized Directories

**Goal**: Prevent path traversal and unauthorized model access.

### Configure Authorized Directories

```bash
# Add to .env
echo "AUTHORIZED_MODEL_DIRS=/Users/wilsonm/.cache/huggingface,/Users/wilsonm/Models" >> .env
```

### Test Path Validation

```bash
# Attempt to load model from unauthorized path (should fail)
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "../../etc/passwd", "messages": [{"role": "user", "content": "test"}]}'
# Expected: 403 Forbidden or 404 Not Found
```

### Verify Symlink Safety

```bash
# Create symlink to test (should be rejected if target outside authorized dirs)
ln -s /etc/passwd /Users/wilsonm/Models/test-model
# Attempt to load "test-model" → Should fail validation
```

---

## Step 3: Protect Sensitive Environment Variables

**Goal**: Ensure API keys and tokens are never logged.

### Enable Redaction

```bash
# Add to .env
echo "REDACT_SENSITIVE_VARS=true" >> .env
```

### Test Redaction

```bash
# Set a sensitive variable
export OPENAI_API_KEY="sk-test123456789"

# Start server and check logs
just run 2>&1 | grep -i "sk-test"
# Expected: No output (key should be redacted to "***REDACTED***")
```

### Secure .env File Permissions

```bash
# Restrict .env to owner only
chmod 600 .env
ls -la .env
# Expected: -rw------- (600)
```

---

## Step 4: Reduce Attack Surface (Disable Non-Essential Endpoints)

**Goal**: Disable endpoints you don't need.

### Disable Unused Endpoints

```bash
# Add to .env (enable only what you need)
echo "DISABLE_HEALTH_ENDPOINT=false" >> .env    # Keep if monitoring
echo "DISABLE_METRICS_ENDPOINT=true" >> .env    # Disable if no Prometheus
echo "DISABLE_MODELS_ENDPOINT=true" >> .env     # Disable if not enumerating models
```

### Verify Endpoints Disabled

```bash
# Start server
just run

# Test disabled endpoints (should return 404 or 403)
curl http://127.0.0.1:8000/metrics
# Expected: 404 Not Found or 403 Forbidden

curl http://127.0.0.1:8000/v1/models
# Expected: 404 Not Found or 403 Forbidden

# Core endpoints should still work
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "your-model", "messages": [{"role": "user", "content": "Hello"}]}'
# Expected: 200 OK with response
```

---

## Step 5: Validate Fail-Closed Behavior

**Goal**: Ensure security failures block server startup.

### Test Invalid Configuration

```bash
# Set invalid model path
echo "AUTHORIZED_MODEL_DIRS=/nonexistent/path" >> .env

# Attempt to start server
just run
# Expected: Server fails to start with clear error message about invalid path
```

### Test Missing Configuration

```bash
# Remove .env temporarily
mv .env .env.bak

# Attempt to start
just run
# Expected: Warning about missing .env, but startup may proceed with defaults
# (Document this behavior)
```

---

## Step 6: API Input Validation Test Examples (US2 - FR-003)

**Goal**: Test input validation rules for API endpoints.

### Test 1: Malformed JSON

```bash
# Send invalid JSON
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "test", "messages": [invalid json}'
# Expected: 422 Unprocessable Entity
```

### Test 2: Oversized Prompt (Exceeds 4096 Characters)

```bash
# Generate a prompt longer than 4096 characters
LONG_PROMPT=$(python3 -c "print('A' * 5000)")

curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{\"model\": \"test\", \"messages\": [{\"role\": \"user\", \"content\": \"$LONG_PROMPT\"}]}"
# Expected: 400 Bad Request with "Prompt too long" message
```

### Test 3: Path Traversal in Input

```bash
# Attempt path traversal in model name
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "../../etc/passwd", "messages": [{"role": "user", "content": "test"}]}'
# Expected: 400 Bad Request with "Invalid input detected"
```

### Test 4: Wrong Content-Type

```bash
# Send with wrong content-type
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: text/plain" \
  -d '{"model": "test", "messages": [{"role": "user", "content": "test"}]}'
# Expected: 415 Unsupported Media Type
```

### Test 5: Shell Metacharacters in Input

```bash
# Attempt command injection in prompt
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "test", "messages": [{"role": "user", "content": "test; rm -rf /"}]}'
# Expected: 400 Bad Request with "Invalid input detected"
```

### Test 6: Empty Request Body

```bash
# Send empty body
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d ''
# Expected: 400 Bad Request
```

---

## Step 7: Path Traversal Test Examples (US3)

**Goal**: Test path traversal prevention for model loading.

### Test 1: Basic Path Traversal

```bash
# Attempt to load model using ../
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "../../etc/passwd", "messages": [{"role": "user", "content": "test"}]}'
# Expected: 403 Forbidden
```

### Test 2: URL-Encoded Path Traversal

```bash
# Attempt URL-encoded traversal
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "..%2F..%2Fetc%2Fpasswd", "messages": [{"role": "user", "content": "test"}]}'
# Expected: 403 Forbidden
```

### Test 3: Absolute Path Outside Authorized Dirs

```bash
# Attempt to load from absolute path outside authorized dirs
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "/etc/passwd", "messages": [{"role": "user", "content": "test"}]}'
# Expected: 403 Forbidden
```

### Test 4: Symlink to Unauthorized Path

```bash
# Create symlink pointing outside authorized dirs
ln -s /etc/passwd /tmp/malicious-model
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "/tmp/malicious-model", "messages": [{"role": "user", "content": "test"}]}'
# Expected: 403 Forbidden (after symlink resolution)
```

---

## Step 8: Environment Variable Security Test Examples (US4)

**Goal**: Test environment variable protection mechanisms.

### Test 1: Verify Redaction in Logs

```bash
# Set multiple sensitive variables
export OPENAI_API_KEY="sk-test123456"
export ANTHROPIC_API_KEY="ant-test789"
export DATABASE_PASSWORD="secret123"

# Start server and check logs for any exposed values
just run 2>&1 | grep -E "sk-test|ant-test|secret123"
# Expected: No output (all should be redacted)
```

### Test 2: Check .env File Permissions

```bash
# Verify .env has correct permissions
stat -f "%Lp" .env  # macOS
# OR on Linux:
stat -c "%a" .env
# Expected: 600

# Try to read .env as another user (if possible)
# Expected: Permission denied
```

### Test 3: Verify Redaction Patterns

```python
# Test redaction function with various sensitive patterns
python3 << 'EOF'
import re

SENSITIVE_PATTERNS = [
    r'.*_KEY$',
    r'.*_TOKEN$',
    r'.*_SECRET$',
    r'.*_PASSWORD$',
    r'.*_CREDENTIAL.*',
]

test_vars = [
    "OPENAI_API_KEY",
    "AWS_SECRET_ACCESS_KEY",
    "DATABASE_PASSWORD",
    "MLX_MODEL_PATH",
    "AUTHORIZED_MODEL_DIRS",
    "SAFE_VARIABLE",
]

for var in test_vars:
    redact = any(re.match(p, var) for p in SENSITIVE_PATTERNS)
    print(f"{var}: {'REDACT' if redact else 'SAFE'}")
EOF
```

### Test 4: Fail-Closed Validation

```bash
# Test with invalid AUTHORIZED_MODEL_DIRS
echo "AUTHORIZED_MODEL_DIRS=" >> .env  # Empty value

# Attempt to start server
just run
# Expected: Warning about empty AUTHORIZED_MODEL_DIRS or fail-closed behavior
```

---

## Step 9: Security Checklist

Run through this checklist after configuration:

- [ ] Server binds to `127.0.0.1` (not `0.0.0.0`)
- [ ] `ALLOW_NETWORK_BINDING=false` (or documented justification if `true`)
- [ ] `AUTHORIZED_MODEL_DIRS` set and validated
- [ ] Path traversal attempts return 403/404
- [ ] Sensitive env vars redacted in logs
- [ ] `.env` file permissions are `600`
- [ ] Non-essential endpoints disabled (if not needed)
- [ ] Core inference endpoints (`/v1/chat/completions`, `/v1/completions`) work
- [ ] Security failures block startup (fail-closed)
- [ ] Input validation rejects malformed JSON, oversized prompts, path traversal, wrong content-type
- [ ] Shell metacharacters in inputs are rejected

---

## Next Steps

1. **Review full documentation**: Read [spec.md](spec.md) and [research.md](research.md)
2. **Update justfile**: Add `just security-check` recipe (see [plan.md](plan.md))
3. **Monitor logs**: Watch for security-related log entries
4. **Test periodically**: Re-run path traversal and security tests after updates
5. **Run security validation**: Execute `just security-check` to validate configuration

---

## Troubleshooting

### Server won't start after security changes
```bash
# Check .env syntax
just lint  # If available, or manually check .env for syntax errors
```

### "Path not authorized" errors
```bash
# Verify authorized dirs exist and are accessible
ls -la $(grep AUTHORIZED_MODEL_DIRS .env | cut -d= -f2)
```

### Sensitive vars still appearing in logs
```bash
# Verify redaction enabled
grep REDACT_SENSITIVE_VARS .env
# Should output: REDACT_SENSITIVE_VARS=true
```

### Input validation not working
```bash
# Check that mlx_lm.server is using Pydantic validation
uv run python -c "import mlx_lm; print(mlx_lm.__version__)"
# Ensure version supports input validation
```
