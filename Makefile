.DEFAULT_GOAL := help

-include .env
export DATABASE_URL ?= postgresql+psycopg://doc-forge:doc-forge@localhost:5432/doc-forge
export DOC_FORGE_ARTIFACT_ROOT ?= ./data
export DOC_FORGE_ENVIRONMENT ?= dev

DOCKER_COMPOSE ?= docker compose

.PHONY: help
help: ## Show this help message
	@echo "Usage: make <target>"
	@echo ""
	@echo "DevEx & Infrastructure Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-25s %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort
	@echo ""
	@echo "Note: Python lifecycle tasks (fmt, test, run-api, etc.) have been moved to poethepoet."
	@echo "      Run 'uv run poe --help' or 'uv run poe <task>' to execute them."

.PHONY: install-git-hooks
install-git-hooks: ## Configure git to use repo-managed hooks
	git config core.hooksPath .githooks

.PHONY: workstream-new
workstream-new: ## Create a new docs workstream with type=<work_type> slug=<slug>
	@if [ -z "$(type)" ] || [ -z "$(slug)" ]; then \
		echo "Usage: make workstream-new type=<work_type> slug=<slug>" >&2; \
		exit 1; \
	fi
	@docs/harness/scripts/new-workstream.sh "$(type)" "$(slug)"

.PHONY: docker-build
docker-build: ## Build the local Docker image for the split runtime
	$(DOCKER_COMPOSE) build

.PHONY: docker-up
docker-up: ## Start the local Docker stack in detached mode
	@eval "$$(uv run python -m doc_forge.devtools.docker_local_generator shell-env)"; \
	run_id="$$(./scripts/prepare_compose_logs.sh)"; \
	echo "compose log run id: $$run_id"; \
	DOC_FORGE_LOG_RUN_ID="$$run_id" $(DOCKER_COMPOSE) up -d

.PHONY: docker-up-build
docker-up-build: ## Build and start the local Docker stack in detached mode
	@eval "$$(uv run python -m doc_forge.devtools.docker_local_generator shell-env)"; \
	run_id="$$(./scripts/prepare_compose_logs.sh)"; \
	echo "compose log run id: $$run_id"; \
	DOC_FORGE_LOG_RUN_ID="$$run_id" $(DOCKER_COMPOSE) up -d --build

.PHONY: docker-down
docker-down: ## Stop the local Docker stack
	$(DOCKER_COMPOSE) down

.PHONY: docker-clean
docker-clean: ## Stop the local Docker stack and remove volumes
	$(DOCKER_COMPOSE) down -v

.PHONY: observability-up
observability-up: ## Start the central eval/log observability stack
	$(DOCKER_COMPOSE) -f docker-compose.observability.yml up -d

.PHONY: observability-up-build
observability-up-build: ## Build and start the central eval/log observability stack
	$(DOCKER_COMPOSE) -f docker-compose.observability.yml up -d --build

.PHONY: observability-down
observability-down: ## Stop the central eval/log observability stack
	$(DOCKER_COMPOSE) -f docker-compose.observability.yml down

.PHONY: docker-logs
docker-logs: ## Show recent API logs from the Docker stack
	$(DOCKER_COMPOSE) logs --tail=120 api

.PHONY: docker-log-index
docker-log-index: ## Show repo-local archived container log locations
	@echo "compose latest:"
	@printf "  %s\n" "$(CURDIR)/data/logs/compose/latest/api.jsonl"
	@printf "  %s\n" "$(CURDIR)/data/logs/compose/latest/worker.jsonl"
	@echo "e2e latest root:"
	@printf "  %s\n" "$(CURDIR)/data/logs/e2e/latest"
	@echo "query context root:"
	@printf "  %s\n" "$(CURDIR)/data/context/queries"

.PHONY: docker-db-shell
docker-db-shell: ## Open a psql shell inside the Docker Postgres service
	$(DOCKER_COMPOSE) exec db psql -U "$${POSTGRES_USER:-doc-forge}" -d "$${POSTGRES_DB:-doc-forge}"
