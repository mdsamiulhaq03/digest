.PHONY: up test lint

up:
	docker compose up --build

test:
	docker compose run --rm app pytest

lint:
	cd backend && ruff check . && ruff format --check .
	cd frontend && npm run lint && npm run typecheck
