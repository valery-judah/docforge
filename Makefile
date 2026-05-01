.DEFAULT_GOAL := help

-include .env
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
	@echo "Note: Python app tasks (fmt, test, run-api, etc.) have been moved to poethepoet."
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
docker-build: ## Build the local Docker image for the API runtime
	$(DOCKER_COMPOSE) build

.PHONY: docker-up
docker-up: ## Start the local Docker stack in detached mode
	@run_id="$$(./scripts/prepare_compose_logs.sh)"; \
	echo "compose log run id: $$run_id"; \
	DOC_FORGE_LOG_RUN_ID="$$run_id" $(DOCKER_COMPOSE) up -d

.PHONY: docker-up-build
docker-up-build: ## Build and start the local Docker stack in detached mode
	@run_id="$$(./scripts/prepare_compose_logs.sh)"; \
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

.PHONY: docker-url
docker-url: ## Resolve the reachable local API base URL
	@uv run python -m doc_forge.devtools.api_discovery

.PHONY: embedding-model-prepare
embedding-model-prepare: ## Prepare a local sentence-transformers model with model=<model_id>
	@if [ -z "$(model)" ]; then \
		echo "Usage: make embedding-model-prepare model=sentence-transformers/all-MiniLM-L6-v2" >&2; \
		exit 1; \
	fi
	uv run python -m doc_forge.devtools.embedding_models "$(model)"

.PHONY: docker-log-index
docker-log-index: ## Show repo-local archived container log locations
	@echo "compose latest:"
	@printf "  %s\n" "$(CURDIR)/data/logs/compose/latest/api.jsonl"
	@echo "e2e latest root:"
	@printf "  %s\n" "$(CURDIR)/data/logs/e2e/latest"
	@echo "query context root:"
	@printf "  %s\n" "$(CURDIR)/data/context/queries"
