.PHONY: dev dev-full test test-all load-test frontend-test lint format migrate down

dev:
	docker compose up -d postgres redis

dev-full:
	docker compose up -d

test:
	uv run pytest tests/unit -v

test-all:
	uv run pytest tests/ -v

load-test:
	uv run pytest tests/load -v

frontend-test:
	cd frontend && npm run lint && npm test && npm run build

lint:
	uv run ruff check . && uv run mypy src/

format:
	uv run ruff format .

migrate:
	uv run alembic upgrade head

down:
	docker compose down
