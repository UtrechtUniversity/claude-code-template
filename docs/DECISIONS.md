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

## D3 — Methodology-first: the shipped stack is one worked example, not the product

**Status:** accepted
**Maturity:** stable
**Date:** 2026-06-01

**Context.** This template seeds agent-coding work across a wide range of projects that do not share a stack — some are PHP web applications, some are Python data pipelines or CLIs, many are existing codebases being extended rather than greenfield builds. A template that hard-bakes one stack as *the* template would force most adopters to delete more than they keep, and would obscure the part that actually transfers.

**Decision.** The product is the **working method**: the principles, documentation discipline, git/PR workflow, the four multi-agent integrity ideas (scope classification, impact filtering with escape hatches, cross-boundary contract check, integration test on single-side PRs), the agent pipeline, and the slash commands/skills. The FastAPI+Svelte+Postgres stack (D1/D2) is retained at the repo root as **one runnable worked example** that keeps the template's own CI green and proves the wiring, but CLAUDE.md, the README, and `docs/ADAPTING.md` frame it as illustrative. Adopters on a different stack delete `backend/` and `frontend/` and re-implement the four ideas in their own tooling.

**Consequences.** The method survives a stack swap; a PHP or data-pipeline adopter keeps CLAUDE.md, docs, `.claude/`, and the agent pipeline unchanged and rewrites only the concrete gauntlet. The cost is that the gauntlet documentation in CLAUDE.md describes machinery many adopters will not run verbatim — mitigated by the explicit "worked example, not a mandate" framing and `docs/ADAPTING.md`. The shipped stack is *not* physically isolated into `examples/`; keeping it at root means the template's own CI exercises it, which is worth the small framing cost (see ADAPTING.md for why a Moodle/PHP adopter still deletes it cleanly).

**Alternatives considered.** Physically relocate `backend/`+`frontend/` into `examples/`: rejected — rewires every CI workflow, the Makefile, `contract_check.py`, and `path_triggers.sh` to non-root paths, and the template would no longer run its own gauntlet at root, weakening the "proves the wiring" value. Strip the demo app entirely and ship only docs: rejected — loses the runnable proof that the multi-agent defenses actually fire, which is the template's most persuasive artifact.
