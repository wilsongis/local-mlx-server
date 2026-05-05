set shell := ["bash", "-c"]

MODEL_PATH := "./models"
HOST := "127.0.0.1"
PORT := "8000"
MAX_TOKENS := "4096"
IMAGE_NAME := "local-mlx-server"
CONTAINER_NAME := "local-mlx-server"

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

# ------------------------------------------------------------------------------
# 3. SECURITY
# ------------------------------------------------------------------------------

# Validate security configuration
security-check:
    @bash scripts/security-check.sh
