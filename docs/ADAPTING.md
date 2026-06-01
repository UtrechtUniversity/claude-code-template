# Adapting this template to your stack

This template ships **one runnable worked example** — FastAPI + Svelte + Postgres — so the multi-agent defenses are concrete and the template's own CI proves they fire. The example is not the point. The point is the **working method** in `CLAUDE.md`, and four CI ideas that transfer to any stack.

If your project is not a FastAPI+Svelte app, this page tells you what to keep, what to delete, and how to re-implement the four ideas in your tooling.

## Keep as-is (stack-agnostic)

These carry over unchanged no matter what you build:

- **`CLAUDE.md`** — principles, "Before Starting" rules, documentation discipline, git/PR workflow, model selection for subagents, GitHub patterns, the agent pipeline. (Rewrite only the `Project` section and the concrete `## Commands` block.)
- **`docs/DECISIONS.md`** and **`docs/design/TEMPLATE.md`** — the decision log and design-doc format. Reset D1/D2 if you drop the shipped stack; keep D3 (methodology-first stance) if it still describes your repo.
- **`.claude/`** — slash commands, skills, schedules (agent pipeline), hooks.
- **`openspec/`** — the capability-spec workflow.
- **Branch protection + PR-only + squash-merge workflow.**

## Delete if you're not using the shipped stack

```
backend/        frontend/        docker-compose.yml
scripts/contract_check.py        scripts/path_triggers.sh   # rewrite, see below
backend/alembic/                 .github/workflows/*.yml     # rewrite, see below
```
Then strip the FastAPI/Svelte/Alembic/testmon/vitest specifics out of `CLAUDE.md`'s `## Commands`, `## Change-scope test gauntlet`, and `## CI gates` sections, replacing them with your stack's equivalents.

## The four ideas, and how to re-implement them

The gauntlet in `CLAUDE.md` is one instantiation of these. Re-implement the *ideas*, not the machinery.

### 1. Scope classification — run only the relevant suites per PR

The template's `detect-scope` job buckets each PR (docs / backend / frontend / full) from changed-file paths and skips suites that can't be affected.

| Your stack | How to classify |
|---|---|
| PHP web app (e.g. a CMS/LMS plugin) | by changed plugin/module directory, and docs-only vs code |
| Python data pipeline / CLI | by changed package vs notebook/docs vs config |
| Monorepo | by top-level package boundary |

Mechanism is just "match changed paths → choose a test subset." A few lines of shell against `git diff --name-only origin/main` plus job-level `if:` guards.

### 2. Impact filtering within a scope — with escape hatches

The template uses `pytest-testmon` (backend) and `vitest --changed` (frontend) so unchanged tests are skipped, **plus carve-outs** for the cases a filter can't see (changed test files always run; fixture-data changes bypass the filter; path-triggered pairings force-include).

- **PHP / PHPUnit**: `--filter` by suite, or group annotations + a changed-path → group map. There is no testmon equivalent; lean on scope classification and path-triggered groups.
- **Python (no testmon)**: `pytest --lf`/`--ff` for local loops; in CI prefer explicit path-triggered selection over a fragile impact filter.
- **JS/TS**: `vitest --changed`, `jest --onlyChanged`.

The non-negotiable part is the **escape hatches**. An aggressive filter that silently skips the one test that should have caught a cross-cut change is worse than no filter. Always: changed test files run; data/fixture changes bypass; keep a source→test trigger map for known couplings.

### 3. A cross-boundary contract check

`scripts/contract_check.py` verifies every frontend API call has a matching backend route and vice versa — catching the case where one agent renames an endpoint and another agent's caller keeps the old name, with both sides' unit tests still green.

Wherever your system has **two sides that must agree but are tested separately**, add a check that compares the two declarations directly:

- REST/RPC client ↔ server: compare the OpenAPI/route table against the client's call sites.
- DB schema ↔ ORM models: a migration-vs-models diff.
- Plugin ↔ host API: assert the plugin only calls host functions that exist in the target version.
- Config schema ↔ config consumers: validate sample configs against the schema in CI.

If your system genuinely has no cross-boundary, drop this idea — but most do.

### 4. An integration test on single-side PRs

The template runs Playwright e2e even on backend-only or frontend-only PRs, because "all unit tests pass in isolation" is not "the wired-up flow works." Whatever your end-to-end path is — an HTTP smoke test, a CLI invocation against a real fixture, a headless browser run, a plugin loaded into a real host instance — run at least a smoke slice of it on every code PR, not only on full ones.

## Migration conflicts (if you have a stateful schema)

D2's `alembic heads` single-head check exists because two agents branching migrations off the same parent each pass their own tests, then the merge produces a schema that won't apply. If your stack has ordered migrations (Rails, Django, Laravel, Flyway, Liquibase, Moodle's `upgrade.php`/`version.php`), add the equivalent "exactly one head / no duplicate version" gate. If your stack has no migrations, drop D2 and this gate.

## What never changes

The reason all of this exists is in `CLAUDE.md` → **Multi-agent integrity defenses**: two agents with different context perspectives, each side's tests green in isolation, `main` broken on merge. Every idea above is a net under that specific failure. Keep that section verbatim — it is the *why* the rest hangs on.
