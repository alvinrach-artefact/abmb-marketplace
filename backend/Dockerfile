FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install dependencies first so this layer is cached between code changes
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .

RUN useradd --create-home appuser
USER appuser

# Cloud Run sets $PORT (defaults to 8080)
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
