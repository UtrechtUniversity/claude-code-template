# Decisions

Single source of truth for architectural and product decisions. Every non-trivial choice gets an entry with rationale and maturity level.

## Format

Each decision:

```
## D<N> — <short title>

**Status:** proposed | accepted | superseded by D<M> | deprecated
**Maturity:** experimental | stable | locked
**Date:** YYYY-MM-DD

**Context.** What problem or constraint prompted this?

**Decision.** What did we choose?

**Consequences.** What does this enable or foreclose? What are the tradeoffs?

**Alternatives considered.** What else was on the table and why it was rejected.
```

## Decisions

## D1 — Stack: FastAPI + SQLAlchemy 2.x async + Postgres + Svelte 5

**Status:** accepted
**Maturity:** stable
**Date:** 2026-05-17

**Context.** The template needs a single fixed stack so adopters can start on multi-agent CI work without spending early effort on stack selection. The stack must be: agent-friendly (well-represented in training data, clear idioms, few magic frameworks), have a real persistence layer (so DB-migration conflicts surface concretely), and exercise a real frontend/backend boundary (so contract drift surfaces concretely).

**Decision.** Python 3.12 + FastAPI on the backend, SQLAlchemy 2.x async + asyncpg against Postgres 17, Alembic for migrations, Svelte 5 + TypeScript + Vite on the frontend, docker-compose for orchestration. uv as the Python package manager; npm for the frontend.

**Consequences.** Agents handle all of these idiomatically — abundant training data, clear typed-ORM and routing patterns. Alembic's linear-history model exposes multi-agent migration conflicts as concrete CI failures (single-head check). The boundary between Svelte/fetch and FastAPI/Pydantic is the substrate for `scripts/contract_check.py`. Postgres-specific behaviour (timezone-aware timestamps, JSON columns, transactional DDL) is preserved end-to-end. Forecloses SQLite-for-everything simplification; that simplification would diverge from realistic deployment and undermine the integration tests.

**Alternatives considered.** SQLite + Flask: rejected — Flask's globals and lack of structured types degrade agent code quality; SQLite hides Postgres-specific failure modes that the template is meant to surface. Django: rejected — too many opinions, larger surface for agents to drift across, ORM/admin/migrations all tangle into one. SQLModel instead of bare SQLAlchemy 2.x: rejected — smaller ecosystem, less StackOverflow signal for agents. React/Vue instead of Svelte: tenable but Svelte 5's compact runes syntax shows up well in PR diffs (less line-noise per behaviour change), which helps reviewers track what an agent actually did.

## D2 — Migrations: Alembic, never schema-from-models in production

**Status:** accepted
**Maturity:** stable
**Date:** 2026-05-17

**Context.** SQLAlchemy can build the schema directly from model metadata via `Base.metadata.create_all`. This is convenient but loses history, makes rollback impossible, and — most importantly for this template — hides the canonical multi-agent failure mode of two parallel migration branches.

**Decision.** Alembic owns the production schema. Each schema change ships as an Alembic revision. `alembic upgrade head` and a single-head check run in CI. Tests use `Base.metadata.create_all` against a throwaway `app_test` database — tests verify code behaviour; Alembic verification is a separate CI step.

**Consequences.** Two agents creating migrations off the same parent revision both pass their own tests, but CI's `alembic heads` check refuses the merge with explicit notice — exactly the conflict the template is built to catch. Schema rollback remains possible. The asyncpg → psycopg2 driver swap in `alembic/env.py` is a real gotcha agents will hit; it's documented inline.

**Alternatives considered.** Skip migrations, regenerate schema each deploy: rejected — hides the multi-agent migration-conflict case the template is built to surface, and is unrealistic for any production system anyway. Alembic with `alembic check` only (no single-head check): rejected — `alembic check` verifies model/DB sync but does not catch sibling revisions; the multi-head case requires the explicit `alembic heads | wc -l` gate.
