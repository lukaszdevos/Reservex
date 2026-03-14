.PHONY: dev dev-full test test-all lint format migrate down

dev:
	docker compose up -d postgres redis

dev-full:
	docker compose up -d

test:
	uv run pytest tests/unit -v

test-all:
	uv run pytest tests/ -v

lint:
	uv run ruff check . && uv run mypy src/

format:
	uv run ruff format .

migrate:
	uv run alembic upgrade head

down:
	docker compose down
