.PHONY: help install-hooks format lint test test-fast migrate run-dev stop-dev logs

help:
	@echo "Targets:"
	@echo "  install-hooks   Enable .githooks as the git hooks path"
	@echo "  run-dev         Start dev environment (docker compose up --build -d)"
	@echo "  stop-dev        Stop dev environment"
	@echo "  logs            Tail dev environment logs"
	@echo "  migrate         Apply Alembic migrations to the dev DB"
	@echo "  format          Auto-format (backend: ruff, frontend: prettier)"
	@echo "  lint            Check formatting / style"
	@echo "  test            Full test suite (backend pytest + frontend vitest) — use before PR go-ahead"
	@echo "  test-fast       TDD loop: pytest -x (fails fast) + vitest"

install-hooks:
	git config core.hooksPath .githooks
	chmod +x .githooks/pre-commit
	@echo "Hooks installed."

# ── Dev environment ───────────────────────────────────────────
run-dev:
	docker compose up --build -d

stop-dev:
	docker compose down

logs:
	docker compose logs -f

# ── Migrations ────────────────────────────────────────────────
# Apply against the running dev DB. depends_on starts the db
# service if not already up; the healthcheck wait makes alembic
# wait for Postgres to be ready.
migrate:
	docker compose run --rm backend alembic upgrade head

# ── Format ────────────────────────────────────────────────────
format:
	docker compose run --rm --no-deps backend sh -c "ruff format src tests && ruff check --fix src tests"
	docker compose run --rm --no-deps frontend npm run format

# ── Lint ──────────────────────────────────────────────────────
lint:
	docker compose run --rm --no-deps backend sh -c "ruff check src tests && ruff format --check src tests"
	docker compose run --rm --no-deps frontend npm run format:check
	docker compose run --rm --no-deps frontend npm run lint

# ── Test ──────────────────────────────────────────────────────
# Full suite — backend tests need the db service (no --no-deps).
test:
	docker compose run --rm backend pytest
	docker compose run --rm --no-deps frontend npm test

# Tight dev-loop variant. pytest -x bails on the first failing
# test for tighter TDD feedback. Frontend tests are unit-level
# (fetch is mocked), so frontend can skip its deps.
test-fast:
	docker compose run --rm backend pytest -x --tb=short
	docker compose run --rm --no-deps frontend npx vitest run
