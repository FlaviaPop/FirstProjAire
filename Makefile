# Local development (uv) and operator shortcuts. Server targets run ON a VM as root, using the
# release currently deployed there (/var/lib/learnplat/current-release).
.PHONY: help lint test translations build up down logs deploy rollback unpin health migrate \
        tf-bootstrap tf-plan tf-apply

RELEASE ?= $(shell cat /var/lib/learnplat/current-release 2>/dev/null)
COMPOSE  = docker compose --project-directory $(RELEASE) -f $(RELEASE)/docker-compose.prod.yml

help:
	@grep -E '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | sed 's/:.*## /\t/'

# --- local -------------------------------------------------------------------------------------
lint: ## Same gates as CI: format, lint, types, import contracts, migrations
	uv run ruff format --check .
	uv run ruff check .
	uv run mypy
	PYTHONPATH=src uv run lint-imports
	uv run python manage.py makemigrations --check --dry-run

translations: ## Compile RO/EN catalogues (needs GNU gettext)
	uv run python manage.py compilemessages --ignore=.venv --ignore=.claude

test: translations ## Full suite with the coverage gate
	uv run pytest -q --cov=src --cov-branch --cov-fail-under=85

build: ## Build the image locally (needs Docker)
	docker build -t ghcr.io/flaviapop/learnplat:local .

# --- on a VM (root) ----------------------------------------------------------------------------
up: ## Start the current release
	LEARNPLAT_IMAGE=$$(cat /var/lib/learnplat/current-image) $(COMPOSE) up -d

down: ## Stop the current release
	LEARNPLAT_IMAGE=$$(cat /var/lib/learnplat/current-image) $(COMPOSE) down

logs: ## Follow app + nginx logs
	LEARNPLAT_IMAGE=$$(cat /var/lib/learnplat/current-image) $(COMPOSE) logs -f --tail=100

deploy: ## Check the GHCR tag now instead of waiting for the timer
	/usr/local/bin/learnplat-watch

rollback: ## Pin and deploy an earlier digest: make rollback IMAGE=ghcr.io/...@sha256:...
	test -n "$(IMAGE)"
	echo "$(IMAGE)" > /var/lib/learnplat/pinned-image
	/usr/local/bin/learnplat-watch

unpin: ## Follow the GHCR tag again after a rollback (fix forward first)
	rm -f /var/lib/learnplat/pinned-image
	/usr/local/bin/learnplat-watch

health: ## Run the container health probe
	LEARNPLAT_IMAGE=$$(cat /var/lib/learnplat/current-image) $(COMPOSE) exec -T app python /app/docker/healthcheck.py && echo healthy

migrate: ## Run migrations (normally automatic at container start)
	LEARNPLAT_IMAGE=$$(cat /var/lib/learnplat/current-image) $(COMPOSE) exec -T app python /app/manage.py migrate --noinput

# --- Terraform (operator laptop) -----------------------------------------------------------------
tf-bootstrap: ## Once: create the state and backup buckets (local state), writes backend.hcl
	cd terraform/bootstrap && terraform init && terraform apply

tf-plan: ## Plan staging + prod
	cd terraform && terraform init -backend-config=backend.hcl && terraform plan

tf-apply: ## Apply staging + prod
	cd terraform && terraform init -backend-config=backend.hcl && terraform apply
