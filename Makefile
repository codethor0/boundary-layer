.PHONY: setup up down test lint smoke demo validate validate-alerts validate-restore-fresh-volume capture-demo validate-prod validate-e2e bug-hunt-prod production-saas-check production-saas-check-example production-saas-auth-smoke production-saas-tenant-isolation-smoke production-saas-staging-readiness-check production-saas-staging-readiness-example production-saas-managed-services-check production-saas-managed-services-example production-saas-managed-services-live-check staging-deploy-dry-run staging-smoke-check staging-smoke-structural staging-smoke-live staging-release-gate infra-validate infra-plan-staging container-image-check bundle clean fmt help prod-render-config prod-up prod-down backup restore

PYTHON ?= python3.12
VENV ?= .venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff
PROD_ENV_FILE ?= .env.production
PROD_COMPOSE := docker compose --env-file $(PROD_ENV_FILE) -f docker-compose.prod.yml -p boundary-layer-prod

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

prod-render-config:
	@test -f $(PROD_ENV_FILE) || (echo "Missing $(PROD_ENV_FILE). Copy .env.production.example first." && exit 1)
	@set -a && . ./$(PROD_ENV_FILE) && set +a && bash deploy/scripts/render-prometheus-config.sh
	@set -a && . ./$(PROD_ENV_FILE) && set +a && bash deploy/scripts/render-alertmanager-config.sh

prod-up: prod-render-config
	$(PROD_COMPOSE) up -d --build
	@echo "Waiting for production stack..."
	@sleep 8
	@curl -k -sf https://localhost:8443/health || (echo "Production health check failed" && exit 1)
	@echo "Production stack is up on https://localhost:8443"

prod-down:
	$(PROD_COMPOSE) down

test:
	$(PYTEST) tests/ -v --tb=short

lint:
	$(RUFF) check apps/ labs/ tests/
	$(RUFF) format --check apps/ labs/ tests/

fmt:
	$(RUFF) format apps/ labs/ tests/

smoke:
	bash scripts/smoke.sh

demo:
	bash scripts/demo.sh

validate:
	bash scripts/validate.sh

validate-alerts:
	bash scripts/validate-alerts.sh

validate-restore-fresh-volume:
	bash scripts/validate-restore-fresh-volume.sh

capture-demo:
	bash scripts/capture-demo-transcript.sh

validate-prod:
	bash scripts/validate-prod.sh

validate-e2e:
	bash scripts/validate-e2e.sh

bug-hunt-prod:
	bash scripts/bug-hunt-prod.sh

production-saas-check:
	bash scripts/production-saas-check.sh

production-saas-check-example:
	bash scripts/production-saas-check-example.sh

production-saas-auth-smoke:
	bash scripts/production-saas-auth-smoke.sh

production-saas-tenant-isolation-smoke:
	bash scripts/production-saas-tenant-isolation-smoke.sh

production-saas-staging-readiness-check:
	bash scripts/production-saas-staging-readiness-check.sh

production-saas-staging-readiness-example:
	bash scripts/production-saas-staging-readiness-example.sh

production-saas-managed-services-check:
	bash scripts/production-saas-managed-services-check.sh

production-saas-managed-services-example:
	bash scripts/production-saas-managed-services-example.sh

production-saas-managed-services-live-check:
	bash scripts/production-saas-managed-services-live-check.sh

staging-deploy-dry-run:
	bash scripts/staging-deploy-dry-run.sh

staging-smoke-check:
	bash scripts/staging-smoke-check.sh

staging-smoke-structural:
	bash scripts/staging-smoke-structural.sh

staging-smoke-live:
	bash scripts/staging-smoke-live.sh

staging-release-gate:
	bash scripts/staging-release-gate.sh

infra-validate:
	bash scripts/infra-validate.sh

infra-plan-staging:
	bash scripts/infra-plan-staging.sh

container-image-check:
	bash scripts/container-image-check.sh

backup:
	bash scripts/backup-postgres.sh

restore:
	@test -n "$(BACKUP)" || (echo "Usage: make restore BACKUP=backups/postgres/file.sql.gz" && exit 1)
	bash scripts/restore-postgres.sh "$(BACKUP)"

bundle:
	bash scripts/collect-bundle.sh

clean:
	bash scripts/clean.sh

help:
	@echo "BoundaryLayer Makefile targets:"
	@echo "  make setup          Create venv and install dependencies"
	@echo "  make up             Start Docker Compose dev stack"
	@echo "  make down           Stop Docker Compose dev stack"
	@echo "  make smoke          Fast sanity check (health, redis pair, metrics)"
	@echo "  make demo           Guided demo with circuit breaker alert poll"
	@echo "  make test           Run pytest"
	@echo "  make lint           Run ruff"
	@echo "  make validate       Full local validation gate (includes validate-alerts)"
	@echo "  make validate-alerts Extended alert delivery (6 deterministic alerts)"
	@echo "  make validate-restore-fresh-volume Fresh-volume Postgres proof (resets local Compose volumes)"
	@echo "  make capture-demo         Generate sanitized docs/assets/demo-transcript.txt"
	@echo "  make validate-prod  Production-like local validation profile"
	@echo "  make production-saas-check Report production-saas readiness (expects NOT READY locally)"
	@echo "  make production-saas-check-example Mocked production-saas readiness pass"
	@echo "  make production-saas-auth-smoke Auth/tenancy unit smoke"
	@echo "  make production-saas-tenant-isolation-smoke Cross-tenant isolation unit smoke"
	@echo "  make production-saas-staging-readiness-check Staging deploy config check (NOT READY locally)"
	@echo "  make production-saas-staging-readiness-example Mocked staging readiness pass"
	@echo "  make production-saas-managed-services-check Managed service policy check (NOT READY locally)"
	@echo "  make production-saas-managed-services-example Mocked managed service structural pass"
	@echo "  make production-saas-managed-services-live-check Live connectivity (requires RUN_LIVE_STAGING_CHECKS=true)"
	@echo "  make staging-deploy-dry-run Staging deploy dry run (no cloud deploy)"
	@echo "  make staging-smoke-check Staging smoke (mode from STAGING_SMOKE_MODE or RUN_LIVE_STAGING_CHECKS)"
	@echo "  make staging-smoke-structural Validate staging smoke env without remote calls"
	@echo "  make staging-smoke-live Live staging HTTP smoke (requires RUN_LIVE_STAGING_CHECKS=true)"
	@echo "  make staging-release-gate Staging release gate with explicit live skip/pass reporting"
	@echo "  make infra-validate Terraform fmt/module skeleton validation"
	@echo "  make infra-plan-staging Terraform plan only (requires CONFIRM_STAGING_PLAN=true)"
	@echo "  make container-image-check Dockerfile/build/local container health smoke"
	@echo "  make validate-e2e   Full test + lint + prod + local validation"
	@echo "  make bundle         Create local review ZIP in ~/Downloads/"
