FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM python:3.12-slim AS runtime
COPY --from=builder /app/.venv /app/.venv
COPY src/ /app/src/
ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app
CMD ["uvicorn", "src.infrastructure.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
