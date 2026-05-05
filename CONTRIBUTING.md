# Contributing to Local MLX Server

Thank you for your interest in contributing to Local MLX Server! This guide will help you get started with the development workflow.

## Getting Started

### Prerequisites

- macOS on Apple Silicon (M1/M2/M3 series)
- [uv](https://docs.astral.sh/uv/) for Python package management
- Git for version control
- Familiarity with MLX and inference infrastructure (helpful but not required)

### Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd local-mlx-server

# Install dependencies using uv
uv sync

# Verify setup
just status
```

### Development Environment

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Verify the server runs
just run
```

## Development Workflow

### Branch Naming Convention

- `feature/` - New features or enhancements
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring without functional changes

### Commit Messages

Follow conventional commit format:

```
<type>(<scope>): <description>

Examples:
feat(server): add model profile switching
fix(quant): correct per-path bit allocation
docs(readme): update operations section
refactor(just): simplify server startup recipe
```

### Spec-Driven Development

This repository uses `/speckit.*` commands for spec-driven development:

```bash
# Start a new feature specification
/speckit.specify

# Plan the implementation
/speckit.plan

# Generate tasks
/speckit.tasks

# Implement the feature
/speckit.implement
```

## Testing Guidelines

### Running Tests

```bash
# Run all tests
just test

# Run specific test file
uv run pytest tests/test_main.py -v

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### Writing Tests

- Place tests in the `tests/` directory
- Follow the `test_<module>.py` naming convention
- Include both positive and negative test cases
- Mock external dependencies (model loading, etc.)

Example test structure:

```python
def test_server_startup():
    """Test that server starts successfully with default config."""
    # Test implementation

def test_invalid_model_path():
    """Test error handling for invalid model path."""
    # Test implementation
```

### Code Style

This project uses:

- **RUFF** for linting and formatting (Python)
- **Markdownlint** for documentation (recommended)

```bash
# Check code style
just lint

# Auto-format code
uv run ruff format .

# Check specific file
uv run ruff check path/to/file.py
```

## Pull Request Process

### Before Submitting

1. Ensure all tests pass: `just test`
2. Run linter: `just lint`
3. Update documentation if needed
4. Add tests for new functionality
5. Verify the server starts: `just run`

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated (if needed)
- [ ] No sensitive information exposed
```

### Review Process

1. PR is reviewed by maintainers
2. Automated checks must pass (tests, linting)
3. At least one maintainer approval required
4. PR is merged after approval and checks pass

## Documentation Standards

When contributing documentation:

- Follow the standards defined in [GOVERNANCE.md](GOVERNANCE.md)
- Use consistent markdown formatting
- Include code examples where appropriate
- Update table of contents if adding new sections
- Verify internal links work correctly

## Security Guidelines for Contributors

When contributing to this infrastructure project, follow these security guidelines:

### Environment Variable Security

- **Never commit `.env` files** - they are in `.gitignore` for a reason
- **Use `.env.example`** - Document all new environment variables with examples
- **Sensitive patterns** - Any variable matching `*_KEY`, `*_TOKEN`, `*_SECRET`, `*_PASSWORD`, `*_CREDENTIAL*` must be treated as sensitive
- **Redaction** - When adding logging, use `REDACT_SENSITIVE_VARS=true` pattern to prevent exposure

### Model Path Security

- **Authorized directories only** - All model paths must be within `AUTHORIZED_MODEL_DIRS`
- **Path traversal prevention** - Reject any path containing `../` or `..\\`
- **Symlink safety** - Resolve symlinks before validation (use `Path.resolve()`)
- **Fail-closed** - Invalid paths must return 403 Forbidden, not expose error details

### Network Security

- **Default localhost-only** - New features should bind to `127.0.0.1` by default
- **Network binding control** - Use `ALLOW_NETWORK_BINDING` environment variable
- **Warning for network exposure** - Document security implications if binding to `0.0.0.0`

### API Input Validation

- **Content-Type validation** - Require `application/json` for all API endpoints
- **Length limits** - Enforce maximum prompt length (4096 chars for this project)
- **Character filtering** - Reject shell metacharacters (`` ` ``, `$()`, `${}`, `|`, `;`, `&&`, `||`)
- **JSON schema validation** - Use Pydantic models for request validation

### Endpoint Security

- **Disable by default** - New non-essential endpoints should be disabled by default
- **Environment control** - Use `DISABLE_*` environment variables for endpoint control
- **Information disclosure** - Be careful about what error messages reveal

### Code of Conduct

- Be respectful and inclusive in all interactions
- Focus on infrastructure-only scope (see [AGENTS.md](AGENTS.md))
- Prioritize memory optimization and serving reliability
- Document operational rationale for inference-related changes
- Use `just` recipes for operational workflows

## Security Checklist for Contributors

Before submitting a PR, verify:

- [ ] No sensitive data in logs (use redaction patterns)
- [ ] Model paths validated against `AUTHORIZED_MODEL_DIRS`
- [ ] Input validation for API endpoints (length, content-type, characters)
- [ ] New endpoints have `DISABLE_*` environment variable control
- [ ] Network binding defaults to localhost (`127.0.0.1`)
- [ ] `.env` file not committed (check `.gitignore`)
- [ ] Security documentation updated (if adding security-related features)
- [ ] `just security-check` passes (if security-related changes)

## Getting Help

- Check [README.md](README.md) for project overview
- Review [OPERATIONS.md](OPERATIONS.md) for operational procedures
- Consult [GOVERNANCE.md](GOVERNANCE.md) for project standards
- Open an issue for questions or bug reports

## Related Documentation

- [README](README.md) - Project overview and navigation index
- [Operations Guide](OPERATIONS.md) - Server operations and `just` recipes
- [Agent Rules](AGENTS.md) - Operational charter for AI agents
- [Governance](GOVERNANCE.md) - Project constitution and documentation standards
- [Security Validation Guide](docs/security-validation.md) - Security patterns and helpers
- [API Endpoint Contracts](specs/002-security-implementation/contracts/api-endpoints.md) - Security contracts
