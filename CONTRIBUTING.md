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

## Code of Conduct

- Be respectful and inclusive in all interactions
- Focus on infrastructure-only scope (see [AGENTS.md](AGENTS.md))
- Prioritize memory optimization and serving reliability
- Document operational rationale for inference-related changes
- Use `just` recipes for operational workflows

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
