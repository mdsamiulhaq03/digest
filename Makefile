.PHONY: up test lint

up:
	docker compose up --build

test:
	pytest

lint:
	ruff check .
	ruff format --check .
