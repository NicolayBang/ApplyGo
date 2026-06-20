# ApplyGo — daily project operations
#
# Canonical, hybrid workflow facade:
#   - Docker Compose owns PostgreSQL, Redis, migrations, and the packaged API/UI.
#   - Local Python/Node tooling supports fast iteration and mirrors the CI gates.
#
# The CI workflow (.github/workflows/ci.yml) remains the source of truth for the
# quality-gate ordering. `make check` only centralizes the same substantive gates.
#
# Conventions:
#   - `make help` (default) lists every public target and its safety behavior.
#   - Named volumes (postgres_data, redis_data) survive `make down`.
#   - `make destroy` is the ONLY volume-removal command and requires CONFIRM=1.
#
# Optional variables:
#   SERVICE=api      restrict `make logs` to one Compose service
#   BACKEND_PORT     host port for health checks / local API (default 8000)
#   CONFIRM=1        required acknowledgement for `make destroy`

SHELL := /bin/bash

COMPOSE      := docker compose
BACKEND_DIR  := backend
FRONTEND_DIR := frontend/app
VENV         := $(BACKEND_DIR)/.venv
VENV_BIN     := $(VENV)/bin
PY           := $(VENV_BIN)/python
PIP          := $(VENV_BIN)/pip
# Path to the venv from inside $(BACKEND_DIR) (recipes that `cd backend` first).
VENV_BIN_REL := .venv/bin

BACKEND_PORT ?= 8000
HEALTH_URL   := http://localhost:$(BACKEND_PORT)/health
UI_URL       := http://localhost:$(BACKEND_PORT)/ui/

.DEFAULT_GOAL := help

.PHONY: help init up upgrade down status logs health destroy \
        infra-up migrate api-dev web-dev build-frontend \
        lint-backend typecheck-frontend test-frontend test-backend test check \
        _require-venv

##@ Help

help: ## List all targets grouped by purpose
	@awk 'BEGIN {FS = ":.*##"; \
		printf "\nApplyGo — make targets\n\nUsage: make <target> [VAR=value]\n"} \
		/^##@/ {printf "\n\033[1m%s\033[0m\n", substr($$0, 5)} \
		/^[a-zA-Z0-9_-]+:.*##/ {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' \
		$(MAKEFILE_LIST)
	@printf "\n\033[1mSafety\033[0m\n"
	@printf "  %-20s %s\n" "make down" "stops containers; PostgreSQL/Redis volumes are PRESERVED"
	@printf "  %-20s %s\n" "make destroy CONFIRM=1" "the ONLY command that deletes database volumes"
	@printf "\n"

##@ Bootstrap

init: ## Idempotent setup: create .env, backend venv, install backend+frontend deps
	@if [ ! -f .env ]; then \
		cp .env.example .env && echo "Created .env from .env.example"; \
	else \
		echo ".env already exists — left unchanged (no values overwritten)"; \
	fi
	@if [ ! -d $(VENV) ]; then \
		python3 -m venv $(VENV) && echo "Created backend virtualenv at $(VENV)"; \
	else \
		echo "$(VENV) already exists — left unchanged"; \
	fi
	$(PY) -m pip install --upgrade pip
	cd $(BACKEND_DIR) && $(VENV_BIN_REL)/pip install -e ".[dev]"
	cd $(FRONTEND_DIR) && npm ci

##@ Lifecycle (Compose packaged app)

up: ## Build and start the packaged API/UI stack (runs migrations via dependency)
	$(COMPOSE) --profile app up -d --build api

upgrade: ## Rebuild/recreate the running app from the working tree and apply migrations (no git fetch, no lockfile changes)
	$(COMPOSE) --profile app build api
	$(COMPOSE) run --build --rm migrate
	$(COMPOSE) --profile app up -d --force-recreate api

down: ## Stop and remove containers; PostgreSQL/Redis volumes are PRESERVED
	$(COMPOSE) down

status: ## Show Compose service status
	$(COMPOSE) ps

logs: ## Tail container logs (optional: SERVICE=api)
	$(COMPOSE) logs -f --tail=100 $(SERVICE)

health: ## Probe the running API /health and /ui/ endpoints
	@echo "GET $(HEALTH_URL)"
	@curl -fsS $(HEALTH_URL) && echo
	@echo "GET $(UI_URL)"
	@curl -fsS -o /dev/null -w "  HTTP %{http_code}\n" $(UI_URL)

destroy: ## DESTRUCTIVE: remove containers AND database volumes (requires CONFIRM=1)
ifeq ($(CONFIRM),1)
	@echo "Removing containers and PostgreSQL/Redis volumes..."
	$(COMPOSE) down -v
else
	@echo "Refusing to destroy: this permanently deletes PostgreSQL and Redis data."
	@echo "Re-run explicitly with: make destroy CONFIRM=1"
	@exit 1
endif

##@ Development (local, fast iteration)

infra-up: ## Start only PostgreSQL and Redis for local backend work
	$(COMPOSE) up -d postgres redis

migrate: ## Apply Alembic migrations against the Compose database
	$(COMPOSE) run --build --rm migrate

api-dev: infra-up migrate _require-venv ## Run FastAPI in reload mode after provisioning infrastructure
	cd $(BACKEND_DIR) && $(VENV_BIN_REL)/python -m uvicorn applypilot.main:app --reload --host 0.0.0.0 --port $(BACKEND_PORT)

web-dev: ## Run the Vite frontend development server
	cd $(FRONTEND_DIR) && npm run dev

build-frontend: ## Build the static dashboard assets served at /ui/
	cd $(FRONTEND_DIR) && npm run build

##@ Validation

lint-backend: _require-venv ## Lint the backend with ruff
	cd $(BACKEND_DIR) && $(VENV_BIN_REL)/python -m ruff check .

typecheck-frontend: ## Type-check the frontend
	cd $(FRONTEND_DIR) && npm run typecheck

test-frontend: ## Run the frontend test suite
	cd $(FRONTEND_DIR) && npm run test

test-backend: infra-up migrate _require-venv ## Run backend tests (auto-starts DB/Redis + migrates; services left running)
	cd $(BACKEND_DIR) && $(VENV_BIN_REL)/python -m pytest

test: test-frontend test-backend ## Run frontend and backend test suites

check: ## Merge-ready CI-equivalent gate (fail fast, non-zero on first failure)
	@echo "==> [1/8] Frontend: install (npm ci)"
	cd $(FRONTEND_DIR) && npm ci
	@echo "==> [2/8] Frontend: typecheck"
	cd $(FRONTEND_DIR) && npm run typecheck
	@echo "==> [3/8] Frontend: test"
	cd $(FRONTEND_DIR) && npm run test
	@echo "==> [4/8] Frontend: build"
	cd $(FRONTEND_DIR) && npm run build
	@echo "==> [5/8] Backend: lint (ruff)"
	$(MAKE) lint-backend
	@echo "==> [6/8] Backend: migrations (alembic upgrade head)"
	$(MAKE) infra-up
	$(COMPOSE) run --build --rm migrate
	@echo "==> [7/8] Backend: tests (pytest)"
	cd $(BACKEND_DIR) && $(VENV_BIN_REL)/python -m pytest
	@echo "==> [8/8] Backend: FastAPI import smoke test"
	cd $(BACKEND_DIR) && $(VENV_BIN_REL)/python -c "from applypilot.main import app; assert app.title == 'ApplyPilot'"
	@echo "==> check: all gates passed"

# Internal: fail early with a helpful message when the backend venv is missing.
_require-venv:
	@test -x $(PY) || { echo "Backend virtualenv missing at $(VENV). Run 'make init' first."; exit 1; }
