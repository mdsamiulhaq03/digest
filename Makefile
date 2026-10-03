.PHONY: up test lint

up:
	docker compose up --build

test:
	docker compose run --rm app pytest

lint:
	ruff check .
	ruff format --check .
