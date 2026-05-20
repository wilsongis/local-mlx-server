set shell := ["bash", "-c"]

MODEL_PATH := "./models"
HOST := "127.0.0.1"
PORT := "8000"
MAX_TOKENS := "4096"
IMAGE_NAME := "local-mlx-server"
CONTAINER_NAME := "local-mlx-server"

# Server Lifecycle Configuration
SERVER_PID_FILE := "/tmp/mlx-server.pid"
SERVER_GRACEFUL_TIMEOUT := "30"
SERVER_LOG_LEVEL := "INFO"

# ------------------------------------------------------------------------------
# 1. CORE EXECUTION
# ------------------------------------------------------------------------------

# Default: Show available commands
default:
    @just --list

# Build container if needed and start the server (containerized)
start:
    @echo "Starting local MLX server container..."
    @if [ ! "$$(podman ps -aq -f name={{CONTAINER_NAME}})" ]; then \
        echo "Container not found, building image..."; \
        just build; \
    fi
    @podman start {{CONTAINER_NAME}} || podman run -d --name {{CONTAINER_NAME}} -p {{PORT}}:{{PORT}} {{IMAGE_NAME}}
    @echo "Server is live at http://{{HOST}}:{{PORT}}"

# Build/Rebuild the container image
build:
    @echo "Building Podman image..."
    podman build -t {{IMAGE_NAME}} .

# Start server natively with mlx_lm.server
run:
    @echo "Starting mlx_lm.server via uv..."
    uv run python -m mlx_lm.server --model {{MODEL_PATH}} --host {{HOST}} --port {{PORT}} --max-kv-size {{MAX_TOKENS}}

# Container status helper
status:
    podman ps -f name={{CONTAINER_NAME}}

# Stop local server container
stop:
    -podman stop {{CONTAINER_NAME}}

# ------------------------------------------------------------------------------
# 2. MAINTENANCE & QUALITY
# ------------------------------------------------------------------------------

# Initialize local virtual environment and editable install
init:
    uv venv
    uv pip install -e .
    @echo "Project initialized."

# Run linting and formatting
lint:
    uv run ruff check . --fix
    uv run ruff format .

# Run the test suite
test:
    uv run pytest

# Verify standard: run linters, formatters, and tests
verify: lint test
    @echo "Verification complete."

# Health check for local MLX server environment
doctor:
    @echo "Running health checks..."
    @echo "Checking uv installation..."
    uv --version || (echo "uv not found. Install from https://docs.astral.sh/uv/getting-started/installation/" && exit 1)
    @echo "Checking mlx_lm availability..."
    uv run python -c "import mlx_lm; print(f'mlx_lm version: {mlx_lm.__version__}')" || (echo "mlx_lm not found. Run 'just init' to install." && exit 1)
    @echo "Checking model path ({{MODEL_PATH}})..."
    [ -d "{{MODEL_PATH}}" ] || (echo "Model path {{MODEL_PATH}} not found. Set MODEL_PATH or create the directory." && exit 1)
    @echo "Checking default port {{PORT}}..."
    lsof -i :{{PORT}} >/dev/null 2>&1 && echo "Warning: Port {{PORT}} is in use." || echo "Port {{PORT}} is free."
    @echo "Health check complete."

# ------------------------------------------------------------------------------
# 3. MLX WRAPPER COMMANDS
# ------------------------------------------------------------------------------

# Start MLX server with specified profile
mlx-start PROFILE="120b-balanced" PRESET="":
    @echo "Starting MLX server with profile: {{PROFILE}}..."
    @uv run python scripts/mlx-wrapper.py start --profile {{PROFILE}} {{if PRESET != ""}}--preset {{PRESET}}{{endif}}

# Stop running MLX server
mlx-stop FORCE="false":
    @echo "Stopping MLX server..."
    @uv run python scripts/mlx-wrapper.py stop {{if FORCE == "true"}}--force{{endif}}

# Check MLX server status
mlx-status:
    @uv run python scripts/mlx-wrapper.py status

# Check MLX server health
mlx-health:
    @uv run python scripts/mlx-wrapper.py health

# List available model profiles
mlx-list-profiles:
    @uv run python scripts/mlx-wrapper.py list-profiles

# List available presets
mlx-list-presets:
    @uv run python scripts/mlx-wrapper.py list-presets

# ------------------------------------------------------------------------------
# 4. SECURITY
# ------------------------------------------------------------------------------

# Validate security configuration
security-check:
    @bash scripts/security-check.sh

# ------------------------------------------------------------------------------
# 5. SERVER LIFECYCLE MANAGEMENT
# ------------------------------------------------------------------------------

# Start MLX server with lifecycle management (PID file, port conflict detection)
server-start MODEL_PATH="{{MODEL_PATH}}":
    @echo "Starting MLX server with lifecycle management..."
    @uv run python scripts/server-lifecycle.py start --pid-file {{SERVER_PID_FILE}} --port {{PORT}} --host {{HOST}} --model {{MODEL_PATH}} --log-level {{SERVER_LOG_LEVEL}} --graceful-timeout {{SERVER_GRACEFUL_TIMEOUT}}

# Stop MLX server with graceful shutdown (SIGTERM -> wait -> SIGKILL)
server-stop:
    @echo "Stopping MLX server with graceful shutdown..."
    @uv run python scripts/server-lifecycle.py stop --pid-file {{SERVER_PID_FILE}} --graceful-timeout {{SERVER_GRACEFUL_TIMEOUT}}

# Check MLX server status (process, health endpoint, uptime)
server-status:
    @uv run python scripts/server-lifecycle.py status --pid-file {{SERVER_PID_FILE}} --port {{PORT}} --host {{HOST}}

# Configure server lifecycle settings (display current configuration)
server-config:
    @echo "Server Lifecycle Configuration:"
    @echo "  PID File: {{SERVER_PID_FILE}}"
    @echo "  Graceful Timeout: {{SERVER_GRACEFUL_TIMEOUT}}s"
    @echo "  Log Level: {{SERVER_LOG_LEVEL}}"
    @echo "  Model Path: {{MODEL_PATH}}"
    @echo "  Host: {{HOST}}"
    @echo "  Port: {{PORT}}"
    @echo ""
    @echo "To change defaults, edit these variables at the top of the justfile:"
    @echo "  SERVER_PID_FILE, SERVER_GRACEFUL_TIMEOUT, SERVER_LOG_LEVEL, MODEL_PATH, HOST, PORT"
