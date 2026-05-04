FROM python:3.12-slim-bookworm

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY . .

RUN groupadd -r appgroup && useradd -r -g appgroup appuser && \
    mkdir -p /app/models && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

LABEL maintainer="Local MLX Server"
LABEL purpose="Local inference infrastructure"

CMD ["uv", "run", "python", "-m", "mlx_lm.server", "--model", "./models", "--host", "0.0.0.0", "--port", "8000", "--max-kv-size", "4096"]