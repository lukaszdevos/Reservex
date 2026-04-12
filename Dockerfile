# ── Stage 1: Build frontend ──────────────────────────────────────
FROM node:22-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Install Python deps ────────────────────────────────
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# ── Stage 3: Runtime ────────────────────────────────────────────
FROM python:3.12-slim AS runtime
COPY --from=builder /app/.venv /app/.venv
COPY src/ /app/src/
COPY --from=frontend /frontend/dist /app/static
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"
WORKDIR /app
CMD uvicorn infrastructure.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
