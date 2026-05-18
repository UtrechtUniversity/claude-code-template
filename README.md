# Agent-coding template

A starting point for projects where multiple coding agents work in parallel against the same codebase. Provides a working FastAPI + Postgres + Svelte stack with CI scaffolding aimed at the failure modes that show up when two agents have different context perspectives: scope detection, testmon, vitest `--changed`, e2e smoke/slow tiers, Alembic single-head check, frontend/backend contract check.

The `items` example exists to prove the stack is wired up. Replace it with your own subject.

## Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.x async + asyncpg, Alembic, Pydantic v2. uv for package management.
- **Database:** Postgres 17, in a docker-compose service.
- **Frontend:** Svelte 5 + TypeScript + Vite. npm for package management.
- **Tests:** pytest (with `pytest-asyncio` + `pytest-testmon`), vitest, Playwright e2e.
- **CI:** GitHub Actions — see `.github/workflows/ci.yml` and `nightly.yml`.

## Day 1 walkthrough

```bash
# 1. Install pre-commit hooks (blocks .env commits, enforces formatters,
#    runs the comment-density check).
make install-hooks

# 2. (Optional) Override host ports if 5432/8000/5173 collide with
#    another dev environment on your machine:
#       cp .env.example .env
#       # edit .env, e.g.  BACKEND_HOST_PORT=8010  FRONTEND_HOST_PORT=5183
#    Container-internal ports stay canonical; only host-side bindings
#    shift. .env is gitignored.

# 3. Start the dev stack (Postgres + backend + frontend).  Backend
#    waits on Postgres's healthcheck, then auto-applies Alembic
#    migrations on startup (see backend/entrypoint.sh).
make run-dev

# 4. Verify the wired-up flow (replace ports with your .env overrides):
#       http://localhost:8000/api/health     → {"status":"ok"}
#       http://localhost:5173/               → the Items page
#    Add a few items via the form; they should persist across
#    `make stop-dev` / `make run-dev` thanks to the pgdata volume.

# 5. Run the tests.
make test

# `make migrate` is also available for manual reruns (e.g. after
# pulling a branch that added new migrations).
```

If any of those steps fail, the bug is in the template itself — please open an issue.

**Running Playwright e2e locally with overridden ports.** The default `PLAYWRIGHT_BASE_URL` is `http://localhost:5173`. When your `.env` sets a different `FRONTEND_HOST_PORT`, export `PLAYWRIGHT_BASE_URL` to match:

```bash
export PLAYWRIGHT_BASE_URL=http://localhost:${FRONTEND_HOST_PORT:-5173}
cd frontend && npm run test:e2e
```

## Day 2: make it yours

1. **Pick a subject.** Replace the `items` example.  Delete:
   - `backend/src/app/routes/items.py`, `backend/src/app/models.py`, `backend/src/app/schemas.py`
   - `frontend/src/lib/Items.svelte`, `frontend/src/lib/api.ts`
   - `backend/tests/test_items.py`, `backend/tests/test_items_integration.py`
   - `frontend/tests/unit/Items.test.ts`, `frontend/tests/unit/api.test.ts`
   - `frontend/tests/e2e/items-flow.spec.ts`
   - `backend/alembic/versions/0001_create_items.py`

2. **Update the path-trigger map.** `scripts/path_triggers.sh` and the table in `CLAUDE.md` → "Slow tier — path triggers" both reference `items` paths.  Replace them with your own source ↔ test mappings as you build them — and keep both in lock-step.

3. **Rewrite the Project section of `CLAUDE.md`.**  It's labelled with a `TEMPLATE NOTE` to make it easy to find.

4. **Reset `docs/DECISIONS.md`.**  Keep D1 (stack) and D2 (Alembic), since those are decisions of the template itself.  Add a D3+ for your own first decision.

## Layout

```
.
├── backend/
│   ├── src/app/                 FastAPI app, async SQLAlchemy, items example
│   ├── tests/                   pytest, including one @pytest.mark.slow test
│   ├── alembic/                 migrations + env.py (asyncpg→psycopg2 swap)
│   └── pyproject.toml
├── frontend/
│   ├── src/                     Svelte 5 (runes) + TypeScript
│   ├── tests/unit/              vitest
│   ├── tests/e2e/               Playwright (smoke + items-flow)
│   └── package.json
├── docker-compose.yml           db + backend + frontend (dev-only)
├── scripts/
│   ├── contract_check.py        frontend API calls vs backend routes
│   └── path_triggers.sh         slow-tier source ↔ test map
├── .github/workflows/
│   ├── ci.yml                   per-PR fast tier with scope detection
│   └── nightly.yml              slow tier + testmon refresh
├── .githooks/
│   ├── pre-commit               format / lint / comment-density gate
│   └── check_comment_density.py
├── .claude/
│   ├── commands/                slash commands (review, design, ticket, ...)
│   ├── skills/                  openspec workflow skills
│   ├── schedules/               sample /schedule routines (agent pipeline)
│   └── hooks/                   PostToolUse hook (issue-close reminder)
├── docs/
│   ├── DECISIONS.md             architectural / product decisions
│   └── design/TEMPLATE.md       design-doc template
├── openspec/                    capability-spec workflow skeleton
├── CLAUDE.md                    agent-facing project guidance
└── Makefile
```

## Where to read next

| If you want to | Read |
|---|---|
| Understand what Claude reads at session start | `CLAUDE.md` |
| Add an architectural decision | `docs/DECISIONS.md` (format documented at the top) |
| Add a new feature larger than a bugfix | `docs/design/TEMPLATE.md` (use `/design`) |
| Understand the CI scope-detection / testmon / vitest --changed logic | `CLAUDE.md` → "Change-scope test gauntlet" |
| Understand the multi-agent integrity defenses | `CLAUDE.md` → "Multi-agent integrity defenses" |
| Set up the agent pipeline (issue → PR auto-merge) | `.claude/schedules/README.md` |

## Requirements

- Docker + Docker Compose
- For local-only development without Docker: Python 3.12, Node 22+, Postgres 17, `uv`.
- GitHub CLI (`gh`) — required for the agent pipeline and many of the workflows documented in `CLAUDE.md`.
