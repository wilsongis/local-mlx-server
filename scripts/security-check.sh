#!/bin/bash
# Security configuration validation script

set -e

echo "Running security configuration check..."

# Check .env.example exists
if [ ! -f .env.example ]; then
    echo "ERROR: .env.example not found"
    exit 1
fi

echo "Checking .env.example..."

# Check required variables
grep -q "ALLOW_NETWORK_BINDING=false" .env.example || (echo "ERROR: ALLOW_NETWORK_BINDING should be false"; exit 1)
grep -q 'MLX_SERVER_HOST="127.0.0.1"' .env.example || (echo "ERROR: MLX_SERVER_HOST should be 127.0.0.1"; exit 1)
grep -q "REDACT_SENSITIVE_VARS=true" .env.example || (echo "ERROR: REDACT_SENSITIVE_VARS should be true"; exit 1)
grep -q "AUTHORIZED_MODEL_DIRS" .env.example || (echo "ERROR: AUTHORIZED_MODEL_DIRS not set"; exit 1)

# Check .env file permissions if it exists
if [ -f .env ]; then
    # macOS
    if stat -f "%Lp" .env 2>/dev/null; then
        perms=$(stat -f "%Lp" .env 2>/dev/null)
    # Linux
    else
        perms=$(stat -c "%a" .env 2>/dev/null)
    fi
    
    if [ "$perms" != "600" ]; then
        echo "WARNING: .env file permissions should be 600 (current: $perms)"
    fi
fi

echo "Security check passed."
