.PHONY: setup up down test lint validate bundle clean fmt

PYTHON ?= python3.12
VENV ?= .venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff

setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r apps/api/requirements-dev.txt
	@echo "Setup complete. Copy .env.example to .env if needed."

up:
	docker compose up -d --build
	@echo "Waiting for services..."
	@sleep 5
	@curl -sf http://localhost:8000/health || (echo "API health check failed" && exit 1)
	@echo "Services are up."

down:
	docker compose down

test:
	$(PYTEST) tests/ -v --tb=short

lint:
	$(RUFF) check apps/ labs/ tests/
	$(RUFF) format --check apps/ labs/ tests/

fmt:
	$(RUFF) format apps/ labs/ tests/

validate:
	bash scripts/validate.sh

bundle:
	bash scripts/collect-bundle.sh

clean:
	bash scripts/clean.sh
