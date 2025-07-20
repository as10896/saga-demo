# syntax=docker/dockerfile:1

FROM python:3.12-slim

WORKDIR /app

# To print directly to stdout instead of buffering output
ENV PYTHONUNBUFFERED=true

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy uv.lock* in case it doesn't exist in the repo
COPY pyproject.toml uv.lock* ./

RUN uv sync --frozen --no-cache

COPY . .

EXPOSE 8000

ENV PORT=8000

# To handle variable expansion (for port forwarding) and signal forwarding (for graceful shutdown) simultaneously
CMD exec uv run -- fastapi run main.py --host 0.0.0.0 --port ${PORT:-8000}
