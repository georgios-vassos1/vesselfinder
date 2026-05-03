.PHONY: build run remove_containers remove_images install lint test clean-cache up down

# --- Docker Compose (TimescaleDB + scraper) ---
up:
	docker compose up -d

down:
	docker compose down

# --- Legacy single-container Podman targets ---
build:
	podman build -t marinetraffic .

run:
	podman run -v ./data:/app/data --rm marinetraffic

remove_containers:
	podman container ls -a | awk 'NR>1 { print $1 }' | xargs podman rm

remove_images:
	podman images | awk 'NR>1 { print $3 }' | xargs podman rmi

# --- Development ---
install:
	uv sync --extra dev

lint:
	uv run ruff check vessel_tracker/ tests/ scripts/

test:
	uv run pytest tests/

clean-cache:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache .venv
	rm -f tests/pytest.log
