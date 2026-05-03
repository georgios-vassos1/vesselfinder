.PHONY: up down logs status build rebuild clean clean-all install lint test

# --- Docker Compose ---
up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f scraper

status:
	docker-compose ps

build:
	docker-compose build scraper

rebuild:
	docker-compose build --no-cache scraper

clean:
	docker-compose down -v
	docker image prune -f

clean-all:
	docker-compose down -v
	docker rmi vessel_track-scraper timescale/timescaledb:latest-pg16 python:3.12-slim-bookworm 2>/dev/null || true
	docker image prune -f

# --- Development ---
install:
	uv sync --extra dev

lint:
	uv run ruff check src/ tests/ scripts/

test:
	uv run pytest tests/

clean-cache:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache .venv
	rm -f tests/pytest.log
