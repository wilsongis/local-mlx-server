# Research: Model Management for Local MLX Server

## Decision Log

### Decision: Model Profile Storage Format
**Decision**: YAML configuration in `scripts/wrapper-config/profiles.yaml`
**Rationale**: Existing infrastructure already uses YAML for profiles and presets. Maintains consistency with current architecture. YAML provides human-readable configuration with support for complex nested structures (quantization paths, inference args).
**Alternatives considered**:
- JSON: Less human-readable, no comments support
- TOML: Not currently used in project, would add new dependency
- SQLite: Overkill for static configuration, adds complexity

### Decision: State Management for Active Model
**Decision**: File-based state using `.active-model` file with flock for concurrency
**Rationale**: Spec requirements explicitly call for file-based locking (flock). Simple, auditable, and doesn't require additional services. File-based state is consistent with "Infrastructure-Only Scope" principle.
**Alternatives considered**:
- Environment variables: Not persistent across sessions
- Process signals: Complex, not persistent
- Database: Over-engineering for single-user local infrastructure

### Decision: Disk Space Validation Approach
**Decision**: Use `psutil` library to check available space on model path and temp directories
**Rationale**: `psutil` is cross-platform, well-maintained, and provides detailed disk usage information. Already commonly used in Python system tools. Provides both path-specific and temporary directory checks.
**Alternatives considered**:
- `shutil.disk_usage`: Limited to path-specific checks, no temp directory awareness
- `df` command parsing: Platform-specific, fragile parsing
- Manual `/System/Volumes/Data` checks: macOS-specific, not portable

### Decision: Model Path Validation Strategy
**Decision**: Check for existence of key model files (config.json, model weights) rather than exhaustive validation
**Rationale**: Per spec assumptions - "Model path validation checks for the existence of key model files (e.g., model weights, configuration)". Exhaustive validation would be slow for large models. Key file presence is a reliable indicator.
**Alternatives considered**:
- Full directory traversal: Too slow for 120B+ models (hundreds of files)
- MLX model loading test: Would actually load model, consuming time and memory
- Hash-based validation: Overhead of computing hashes on large files

### Decision: Concurrent Access Protection
**Decision**: Use `fcntl.flock()` on the state file for exclusive access during model switches
**Rationale**: Spec requirement explicitly states "File-based locking (flock)". Simple, kernel-level locking. Works across Python processes on same system. Automatic lock release on process crash.
**Alternatives considered**:
- File existence locks (`.lock` files): Race condition prone
- SQLite with transactions: Overkill for single file state
- Redis/distributed locks: Requires additional infrastructure

### Decision: Integration with Existing just Commands
**Decision**: Add `models-list` and `model-use` recipes to existing justfile
**Rationale**: Constitution Principle IV mandates "Just Command Bridge". Existing justfile already has `mlx-start`, `mlx-stop` commands. Consistent with current operational interface.
**Alternatives considered**:
- Separate CLI tool: Would duplicate just functionality
- Python entry point script: Less discoverable than just recipes
- Makefile: Project already standardized on just

## Best Practices Research

### Model Profile Configuration
- **Structure**: Use list of profiles with unique `name` field for identification
- **Validation**: Validate required fields (name, model_path) on load
- **Extensibility**: Design for additional fields without breaking changes
- **Documentation**: Include `description` field for user-friendly display

### File-Based State Management
- **Atomic writes**: Write to temp file, then rename to avoid partial state
- **Error handling**: Handle missing state file gracefully (no active model)
- **Permissions**: Ensure state file is readable/writable by user
- **Location**: Store in project root or configurable path

### CLI Command Design
- **Idempotency**: `models-list` should be safe to run multiple times
- **Clear output**: Use consistent formatting (tables or aligned columns)
- **Exit codes**: Return non-zero on validation failures
- **Error messages**: Actionable errors with suggested fixes

### Disk Space Checks
- **Threshold configuration**: Make warning/critical thresholds configurable
- **Multiple paths**: Check model path and temp directory (for KV cache)
- **Units**: Display in GB with 1 decimal precision for readability
- **Warnings vs errors**: Warn on low space, error only on critical shortage

## Technical Context Resolved

All NEEDS CLARIFICATION items from Technical Context have been resolved:
- ✅ Language/Version: Python 3.11+ (from existing project)
- ✅ Primary Dependencies: mlx-lm, pyyaml, psutil (identified)
- ✅ Storage: File-based (profiles.yaml, .active-model)
- ✅ Testing: pytest (existing framework)
- ✅ Target Platform: macOS Apple Silicon (existing)
- ✅ Project Type: CLI/infrastructure (just recipes + Python)
- ✅ Performance Goals: < 2s list, < 5s switch (from spec)
- ✅ Constraints: Memory-constrained, file-based locking (defined)
- ✅ Scale/Scope: 3 profiles initially, extensible (defined)
