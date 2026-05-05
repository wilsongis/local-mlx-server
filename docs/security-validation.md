# Security Validation Guide

This document describes security validation patterns and helper functions for the Local MLX Server infrastructure.

## Path Validation

### Authorized Model Directory Validation

When loading models, validate that the requested path falls within authorized directories:

```python
from pathlib import Path
import os

def is_authorized_model_path(requested_path: str, authorized_dirs: list[str]) -> bool:
    """
    Validate that a requested model path is within authorized directories.
    
    Args:
        requested_path: The path to validate (may be relative or absolute)
        authorized_dirs: List of authorized directory paths
    
    Returns:
        True if path is authorized, False otherwise
    """
    try:
        # Resolve to absolute path, resolving symlinks
        resolved = Path(requested_path).resolve()
        
        # Check against each authorized directory
        for auth_dir in authorized_dirs:
            auth_resolved = Path(auth_dir).resolve()
            # Ensure requested path is within authorized directory
            # Use prefix matching on resolved absolute paths
            if str(resolved).startswith(str(auth_resolved)):
                return True
        return False
    except (OSError, RuntimeError):
        # Fail closed on any resolution error
        return False
```

### Path Traversal Prevention

Reject paths containing traversal patterns:

```python
import re

def contains_traversal_pattern(path: str) -> bool:
    """
    Check if path contains directory traversal patterns.
    
    Returns:
        True if traversal pattern detected, False otherwise
    """
    # Check for ../ or ..\\ patterns
    if re.search(r'\.\.[/\\]', path):
        return True
    # Check for absolute paths if only relative allowed
    if os.path.isabs(path) and not os.path.isabs(requested_path):
        return True
    return False
```

## Environment Variable Redaction

### Sensitive Pattern Detection

Patterns to redact from logs and error messages:

```python
import re
from typing import Dict

# Sensitive variable patterns (by prefix/name)
SENSITIVE_PATTERNS = [
    r'.*_KEY$',           # API keys
    r'.*_TOKEN$',         # Tokens
    r'.*_SECRET$',        # Secrets
    r'.*_PASSWORD$',      # Passwords
    r'.*_CREDENTIAL.*',   # Credentials
    r'MLX_MODEL_PATH',    # Model paths may be sensitive
    r'AUTHORIZED_MODEL_DIRS',
]

def should_redact(var_name: str) -> bool:
    """
    Check if an environment variable should be redacted.
    
    Args:
        var_name: Environment variable name
    
    Returns:
        True if variable should be redacted
    """
    for pattern in SENSITIVE_PATTERNS:
        if re.match(pattern, var_name):
            return True
    return False

def redact_env_value(var_name: str, value: str) -> str:
    """
    Redact sensitive environment variable values.
    
    Args:
        var_name: Variable name
        value: Current value
    
    Returns:
        Redacted value (original if not sensitive)
    """
    if should_redact(var_name):
        return '***REDACTED***'
    return value
```

## Network Binding Validation

### Localhost-Only Default

Ensure server binds to localhost by default:

```python
def validate_host_binding(host: str, allow_network: bool) -> str:
    """
    Validate and return the host binding configuration.
    
    Args:
        host: Requested host address
        allow_network: Whether network binding is allowed
    
    Returns:
        Validated host address
    
    Raises:
        ValueError: If network binding requested but not allowed
    """
    if not allow_network and host not in ('127.0.0.1', 'localhost', '::1'):
        raise ValueError(
            f"Network binding not allowed. "
            f"Set ALLOW_NETWORK_BINDING=true to bind to {host}"
        )
    return host
```

## Fail-Closed Behavior

All security validations must fail closed:

- **Path validation fails**: Reject model load, return 403 Forbidden
- **Env var validation fails**: Redact value, log warning
- **Network binding validation fails**: Refuse to start server
- **Input validation fails**: Return 400 Bad Request

## Usage in mlx_lm.server Context

These validation patterns are designed to work with `mlx_lm.server` OpenAI-compatible interface. They should be applied:

1. Before server startup (host binding, env var validation)
2. During model loading (path validation)
3. During request processing (input validation, redaction in logs)

No modifications to `mlx_lm.server` code are required—these are infrastructure-level validations documented for operators.
