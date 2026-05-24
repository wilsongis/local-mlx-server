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

# KV Cache Compression Configuration
KV_CACHE_PROFILE := "auto"
KV_CACHE_BITS := "3"
KV_CACHE_GROUP_SIZE := "64"

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
    @uv run python scripts/mlx-wrapper.py start --profile {{PROFILE}}

# Stop running MLX server
mlx-stop:
    @echo "Stopping MLX server..."
    @uv run python scripts/mlx-wrapper.py stop

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
server-start MODEL_PATH="{{MODEL_PATH}}" KV_PROFILE="{{KV_CACHE_PROFILE}}":
    @echo "Starting MLX server with lifecycle management..."
    @uv run python scripts/server-lifecycle.py start --pid-file {{SERVER_PID_FILE}} --port {{PORT}} --host {{HOST}} --model {{MODEL_PATH}} --log-level {{SERVER_LOG_LEVEL}} --graceful-timeout {{SERVER_GRACEFUL_TIMEOUT}} --kv-cache-profile {{KV_PROFILE}}

# Stop MLX server with graceful shutdown (SIGTERM -> wait -> SIGKILL)
server-stop:
    @echo "Stopping MLX server with graceful shutdown..."
    @uv run python scripts/server-lifecycle.py stop --pid-file {{SERVER_PID_FILE}} --graceful-timeout {{SERVER_GRACEFUL_TIMEOUT}}

# Check MLX server status (process, health, uptime)
server-status JSON_FLAG="":
    @uv run python scripts/server-lifecycle.py status --pid-file {{SERVER_PID_FILE}} --port {{PORT}} --host {{HOST}} {{JSON_FLAG}}

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
    @echo "KV Cache Compression Configuration:"
    @echo "  Profile: {{KV_CACHE_PROFILE}}"
    @echo "  Bits: {{KV_CACHE_BITS}}"
    @echo "  Group Size: {{KV_CACHE_GROUP_SIZE}}"
    @echo ""
    @echo "To change defaults, edit these variables at the top of the justfile:"
    @echo "  SERVER_PID_FILE, SERVER_GRACEFUL_TIMEOUT, SERVER_LOG_LEVEL, MODEL_PATH, HOST, PORT"
    @echo "  KV_CACHE_PROFILE, KV_CACHE_BITS, KV_CACHE_GROUP_SIZE"

# ------------------------------------------------------------------------------
# 6. MODEL MANAGEMENT
# ------------------------------------------------------------------------------

# List all available model profiles
models-list JSON_FLAG="":
    @uv run python scripts/model-management.py list {{JSON_FLAG}}

# Activate a model profile for serving
model-use PROFILE="" VALIDATE="true" FORCE="false":
    @if [ "{{FORCE}}" = "true" ]; then \
        uv run python scripts/model-management.py use {{PROFILE}} --force; \
    elif [ "{{VALIDATE}}" = "true" ]; then \
        uv run python scripts/model-management.py use {{PROFILE}} --validate; \
    else \
        uv run python scripts/model-management.py use {{PROFILE}}; \
    fi

# Show currently active model profile
model-status:
    @uv run python scripts/model-management.py status

# Check model-status before server startup
mlx-start-check:
    @echo "Checking model status before startup..."
    @just model-status
    @echo "Starting MLX server with lifecycle management..."
    @uv run python scripts/server-lifecycle.py start --pid-file {{SERVER_PID_FILE}} --port {{PORT}} --host {{HOST}} --log-level {{SERVER_LOG_LEVEL}} --graceful-timeout {{SERVER_GRACEFUL_TIMEOUT}}

# ------------------------------------------------------------------------------
# 7. QUANTIZATION MANAGEMENT (Spec 007)
# ------------------------------------------------------------------------------

# List available quantization profiles
quant-list:
    @uv run python -c "import yaml; data = yaml.safe_load(open('scripts/wrapper-config/profiles.yaml')); profiles = data.get('quantization_profiles', {}); print('Available Quantization Profiles:'); [print(f'  - {k} (attention: {v[\"attention_bits\"]}-bit, expert: {v[\"expert_bits\"]}-bit, group: {v[\"group_size\"]})') for k, v in profiles.items()]"

# Validate a quantization profile
quant-validate PROFILE="":
    @if [ -z "{{PROFILE}}" ]; then echo "Usage: just quant-validate <profile>"; exit 1; fi
    @uv run python scripts/quantization/cli_helper.py validate --profile {{PROFILE}}

# Apply quantization profile to a model
quant-apply MODEL="" PROFILE="":
    @if [ -z "{{MODEL}}" ] || [ -z "{{PROFILE}}" ]; then echo "Usage: just quant-apply <model> <profile>"; exit 1; fi
    @echo "Applying quantization profile '{{PROFILE}}' to model '{{MODEL}}'..."
    @uv run python scripts/quantization/cli_helper.py apply --model {{MODEL}} --profile {{PROFILE}}

# Show current quantization status for active model
quant-status:
    @uv run python -c "from scripts.mlx_wrapper import health_status; import json; quant = health_status.get('quantization', {}); print('Quantization Status:'); print(json.dumps(quant, indent=2))"

# Run Lloyd-Max calibration with provided dataset
quant-calibrate DATASET="" OUTPUT="":
    @if [ -z "{{DATASET}}" ] || [ -z "{{OUTPUT}}" ]; then echo "Usage: just quant-calibrate <dataset> <output>"; exit 1; fi
    @echo "Running Lloyd-Max calibration with dataset: {{DATASET}}"
    @uv run python -c "from scripts.quantization.lloyd_max import LloydMaxCalibrator; import numpy as np; calibrator = LloydMaxCalibrator(bits=3, group_size=32); data = calibrator.load_calibration_data('{{DATASET}}'); codebook = calibrator.generate_codebook(data); path = calibrator.save_codebook('{{OUTPUT}}'); print(f'Codebook generated: {path}'); print(f'Perplexity improvement: {calibrator.perplexity_improvement:.2f}%')"

# ------------------------------------------------------------------------------
# 8. KV CACHE COMPRESSION (Spec 008)
# ------------------------------------------------------------------------------

# Show KV cache compression status
kv-status:
    @uv run python -c "from scripts.quantization.kv_cache_compression import KVCacheCompressionManager; import json; manager = KVCacheCompressionManager({'enabled': True, 'profile': '{{KV_CACHE_PROFILE}}'}); status = manager.get_status(); print('KV Cache Compression Status:'); print(json.dumps(status, indent=2))"

# Enable KV cache compression with specified profile
kv-enable PROFILE="{{KV_CACHE_PROFILE}}" BITS="{{KV_CACHE_BITS}}" GROUP_SIZE="{{KV_CACHE_GROUP_SIZE}}":
    @echo "Enabling KV cache compression with profile: {{PROFILE}}..."
    @echo "  Bits: {{BITS}}"
    @echo "  Group Size: {{GROUP_SIZE}}"
    @uv run python -c "from scripts.quantization.kv_cache_compression import KVCacheCompressionManager; manager = KVCacheCompressionManager({'enabled': True, 'profile': '{{PROFILE}}', 'default_bits': {{BITS}}, 'default_group_size': {{GROUP_SIZE}}}); manager.enable('{{PROFILE}}'); print(f'KV cache compression enabled with profile: {{PROFILE}}')"

# Disable KV cache compression
kv-disable:
    @echo "Disabling KV cache compression..."
    @uv run python -c "from scripts.quantization.kv_cache_compression import KVCacheCompressionManager; manager = KVCacheCompressionManager({'enabled': False}); manager.disable(); print('KV cache compression disabled')"

# List available KV cache profiles
kv-list-profiles:
    @uv run python -c "import yaml; data = yaml.safe_load(open('scripts/wrapper-config/kv-cache-profiles.yaml')); profiles = data.get('kv_cache_profiles', {}); print('Available KV Cache Profiles:'); [print(f'  - {k}: {v.get(\"description\", \"\")}') for k, v in profiles.items()]"

# Validate KV cache profile configuration
kv-validate PROFILE="{{KV_CACHE_PROFILE}}":
    @echo "Validating KV cache profile: {{PROFILE}}..."
    @uv run python -c "from scripts.quantization.config_builder import QuantizationConfigBuilder; from scripts.quantization.kv_cache_profiles import CompressionProfile; config = {'enabled': True, 'profile': '{{PROFILE}}'}; profile = QuantizationConfigBuilder.parse_kv_cache_config(config); print(f'Profile: {profile.name if profile else \"disabled\"}'); print(f'Path: {profile.path if profile else \"N/A\"}'); print(f'Bits: {profile.bits if profile else \"N/A\"}'); print(f'Valid: {profile is not None}')"
