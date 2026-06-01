# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. It is read at the start of every session and treated as authoritative.

## Project

> **TEMPLATE NOTE — replace this section.** Describe your project in one paragraph: what it does, who it serves, what the MVP delivers. Keep it tight; if the reader wants more, point at `docs/`.

**What this template is.** The product is the *working method* below — principles, doc discipline, git workflow, the multi-agent integrity defenses, and the agent pipeline. That method is stack-agnostic and is the part you keep no matter what you build.

The repo also ships **one worked example stack** to make the method concrete and prove the wiring runs end-to-end: FastAPI + Python backend, SQLAlchemy 2.x async + Alembic against Postgres, Svelte 5 + TypeScript + Vite frontend, all via docker-compose, with a deletable `items` example. **If your project uses a different stack** (PHP, a data pipeline, a CLI, an existing codebase you're extending), the concrete commands and CI gauntlet below are illustrations, not requirements — read `docs/ADAPTING.md` for how to map the same ideas onto your stack, then delete `backend/` and `frontend/`.

## Principles

**Single source of truth.** Every rule, convention, and decision is defined in exactly one place. This file points to those places — it does not repeat them. When in doubt, the source doc wins. If two docs disagree, flag it as a bug.

**Consistency over novelty.** Before introducing a new pattern, check `docs/DECISIONS.md` for existing decisions. If the new approach contradicts a settled decision, ask before proceeding. Record every new decision with rationale.

**Ask when ambiguous.** If a task requires a decision not covered by existing docs, ask rather than guessing. Then record the answer in `docs/DECISIONS.md`.

**Trust user observations on rendered output — reproduce at the level the user is looking at.** When the user reports wrong behaviour in a *rendered surface* (a web page, dashboard, PDF or report export, chart, generated document), treat it as a real bug by default. "Optical illusion", "rendering artifact", "stale cache", "could you zoom in?", "the data layer is correct" are suspicious first responses, not investigations. Verify by reproducing at the same level the user is looking at: if they are looking at a rendered PDF, render the PDF and inspect it; if they are looking at a page, load the page; if they are counting items on screen, count them on the rendered output, not on the input data. Data-level verification does **not** exonerate the transform / render / pipeline layer — bugs live there too. This rule applies to **rendered/visual output specifically**; for pure data, logs, git operations, contract checks, and CI signals, retain default confidence and follow the evidence.

## Before Starting ANY Implementation

**MANDATORY first steps — never skip these:**

1. Read `docs/DECISIONS.md` for relevant decisions.
2. Read any domain-specific guideline docs under `docs/` that apply to the area you are touching.
3. When spawning design/UX agents, include the relevant guidelines and decisions in their prompts so they design within the existing system — not from scratch.
4. **For non-trivial work, write a design doc BEFORE coding.** "Non-trivial" means: a new feature, a new module boundary, anything where the "why" and rejected alternatives would not be obvious from the code diff alone. Bug fixes and minor refactors do NOT trigger this rule.
   - Use `/design <feature-name>` to create a doc from `docs/design/TEMPLATE.md`.
   - Either form must capture: the problem, options considered, option chosen, rejected alternatives, and why. Link from a new entry in `docs/DECISIONS.md` if the choice qualifies as an architectural decision.

## Commands

```bash
make test                # full test suite (use before opening a PR)
make test-fast           # tight TDD loop: pytest -x + vitest, --no-deps
make format              # auto-format
make lint                # formatting/style checks
make run-dev             # start dev environment (db + backend + frontend)
make stop-dev            # stop dev environment
make logs                # tail dev logs
make migrate             # apply Alembic migrations to the dev DB
make install-hooks       # enable pre-commit hooks
```

## Automated checks

Pre-commit hooks (`make install-hooks`) block `.env` commits, enforce comment-density limits on staged Python (per the no-bloat policy in "Documentation discipline" below), and run **ruff format --check + ruff check** on staged Python and **prettier --check** on staged TS/Svelte/CSS/HTML. CI re-runs the same checks (plus the full test gauntlet) as a safety net.

**Never skip hooks.** Do not use `--no-verify`. Fix the underlying issue instead.

## Static checks during agent sessions

Static analysis tools split into roles. Knowing **when** to run each prevents burning cycles on code that's about to be rewritten.

| Role | Tool | When to run |
|---|---|---|
| **Formatters** (appearance only) | prettier, ruff format | Never in-loop. Pre-commit hook is the gate. |
| **Lint** (pattern rules) | ruff check | Never in-loop. Pre-commit hook is the gate. |
| **Type checks** (correctness) | mypy, tsc, svelte-check | On-demand at *inflection points* — not reflexively. |
| **Contract check** (cross-side agreement) | `scripts/contract_check.py` | On-demand at inflection points. |
| **DB migrations** | `alembic upgrade head` + `alembic heads` | After any model change, before committing. |
| **Tests** | pytest, vitest, Playwright | Hold until the user has confirmed behaviour in the browser; then run the change-scope gauntlet before filing the PR. |

**Inflection points** mean: after a function-signature change, after a refactor touching multiple files, after wiring up a new endpoint, before declaring a feature "done". *Not* after every edit during exploratory iteration.

Test suites are also held back during iteration. Wait until the user has checked behaviour in the browser before running the suite — this avoids burning cycles on code that's likely about to change. Internal verification (printing function output, asserting on intermediate values) stays fine.

## Slash commands

| Command | When to use |
|---------|-------------|
| `/review` | Before creating a PR — checks decisions, security, tests |
| `/design` | Before building a non-trivial feature — creates a design doc from template |
| `/ticket` | To create a well-structured GitHub issue |
| `/audit-decisions` | To check if changes are consistent with all recorded decisions |
| `/audit-security` | To check for OWASP, auth, permissions, and data exposure issues |
| `/test-plan` | To generate test scenarios for a feature or change |
| `/post-issue-transcript` | Post a user/Claude transcript as an issue comment at PR-open / issue-close |
| `/opsx:propose` | Propose a new capability change with full artifacts |
| `/opsx:explore` | Think through ideas and clarify requirements before proposing |
| `/opsx:apply` | Implement tasks from an OpenSpec change |
| `/opsx:archive` | Archive a completed OpenSpec change |

## Sources of truth

| Doc | Governs | When to check |
|-----|---------|---------------|
| `docs/DECISIONS.md` | All architectural and product decisions with rationale and maturity level | Before implementing anything. Before making a judgment call. |
| `docs/design/TEMPLATE.md` | Structure for feature design docs | When creating a new design doc (`/design` command) |
| `docs/design/*.md` | Feature design docs with implementation status | Commit design docs to the repo. Update their status as work progresses. |
| `openspec/specs/**/spec.md` | Capability contracts with REQ-* identifiers | Before writing or modifying tests or features tied to a capability |

## Documentation discipline — no invented justifications

Design docs, DECISIONS.md entries, commit bodies, and PR descriptions are treated as load-bearing project context by successor agents. **If the user or issue does not state a reason, do not invent one.**

"Issue requires X" is a complete justification. "Spec asks for X" is complete. A code citation is complete. Made-up domain rationale — "industry standard", "best practice", invented stakeholder concerns — is not, even when it sounds plausible. The next agent reads invented backstory as established context and designs follow-on work around the fabricated premise.

The same rule rules out **verbose padding that has no source**: field-by-field listings duplicating code, ASCII mockups duplicating the running UI, multi-line "Why" prose restating the decision in different words. Respect the 20-line-per-section budget in `docs/design/TEMPLATE.md`.

In code: default to no comments. Only comment where the WHY isn't obvious — a hidden constraint, a workaround, a non-obvious invariant. The pre-commit hook (`.githooks/check_comment_density.py`) enforces this: a staged Python file cannot add more comment/docstring lines than code lines. This is the multi-agent defense against doc-bloat: agents read the closest comment first, and paraphrased prose drifts from source-of-truth docs.

## Git workflow

Branch: `<type>/<issue#>-<short-description>` (types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `ci`)

Commits: [Conventional Commits](https://www.conventionalcommits.org/) with optional `(<scope>)`. Subject under 72 chars. Body for *why*.

**All changes go through a PR** — never commit directly to `main`. Squash merge only. One logical change per PR.

### Starting an issue ("#42" / "start 42")

When the user references an issue number as a starting instruction, interpret it as the full procedure:

1. **Check local cleanup needed.** `git status`. If the working tree has uncommitted work or you're on a non-main branch with unpushed work, stop and confirm before discarding or stashing.
2. **Pull `main`.** `git checkout main && git pull` so the new branch starts from the latest tip.
3. **Read the issue.** Fetch via `gh issue view <n> --json number,title,state,body,labels`. Pass `--json` explicitly to avoid the GraphQL Projects-classic 500 error.
4. **Process labels.**
   - **Stop and tell the user** if `in-progress`, `blocked`, `wontfix`, `duplicate`, or `invalid` is set.
   - **Surface to the user before continuing** if `failed`, `needs-decision`, or `backlog` is set.
   - Otherwise mark in progress and drop the pickup flag: `gh issue edit <n> --add-label in-progress --remove-label ready`.
5. **Make an appropriately named local branch.** `<type>/<n>-<short-description>` (type inferred from issue body / category label: `bug` → `fix/`, `documentation` → `docs/`, `enhancement` → `feat/`).
6. **Start the issue.** Then follow the commit / push / PR cadence below.
7. **Hold lint and pytest** until the user has checked behaviour in the browser — see "Static checks during agent sessions".

### Commit / push / PR cadence

Agents implementing work follow this cadence:

1. **Commit and push as you go.** Each logical chunk of work gets a commit pushed to `origin/<branch>`. Pushing keeps work visible and recoverable.
2. **Move on or pause — do not open a PR.** Continue to the next piece, or pause for confirmation when the next step is ambiguous.
3. **Wait for explicit PR go-ahead.** "Open the PR", "ship it", "file the PR", or `/review` followed by approval count as go-ahead. Absent that, do not run `gh pr create`.
4. **Once go-ahead is given, run the local test gauntlet matching your change scope** (see below). Do not file a PR with known-failing local tests on the assumption CI will catch it later.
5. **File the PR only after local tests pass** for that scope.

Before pushing to an existing branch/PR, **always check if the PR has already been merged** via `gh pr view <n> --json state,mergedAt`.

## Change-scope test gauntlet

> **Worked example, not a mandate.** Everything in this section is the gauntlet for *this template's* FastAPI+Svelte+Postgres stack. The transferable ideas are four: (1) **classify each PR by scope** and run only the relevant suites; (2) **impact-filter within a scope** so unchanged tests are skipped, with escape hatches for the cases a filter can't see; (3) **a cross-boundary contract check** so two sides can't drift apart silently; (4) **an integration test on single-side PRs**, because unit tests passing in isolation does not mean the wired-up flow works. Re-implement those four ideas in your stack's tooling — see `docs/ADAPTING.md`. The concrete `pytest`/`vitest`/`alembic` machinery below is one instantiation.

Not every PR needs the full gauntlet. The `detect-scope` job in `.github/workflows/ci.yml` classifies each PR into one of four buckets and gates the other CI jobs accordingly. Run the same subset locally before filing.

| Scope | backend-test | frontend-test | e2e-test | contract-check |
|-------|:---:|:---:|:---:|:---:|
| **docs**     | skip | skip | skip | skip |
| **backend**  | run  | skip | run  | run  |
| **frontend** | skip | run  | run  | run  |
| **full**     | run  | run  | run  | run  |

**Allowlist patterns** (lock-step with the `detect-scope` job — change both together):

- **docs**: `**/*.md`, `docs/`, `openspec/`, `.claude/`, `LICENSE`, `.gitignore`, `.editorconfig`
- **backend**: `backend/` + `scripts/contract_check.py`
- **frontend**: `frontend/`
- **full** is forced by: any file outside the three allowlists, or a PR that touches both `backend/` and `frontend/`.

**Why e2e runs for single-side PRs.** A backend-only refactor can break the wired-up flow even if backend unit tests pass; same for frontend. e2e is the integration safety net. `contract_check.py` similarly catches schema drift between the two sides regardless of which one moved.

When in doubt, run more rather than less. The fast path is for *clearly* docs / single-side changes; mixed PRs always run full.

### Testmon filter (backend-test only)

Within the backend bucket, `pytest-testmon` records per-test source-block fingerprints in `backend/.testmondata` and deselects tests whose Python deps are unchanged since the cached fingerprint.

- **Cache** — `actions/cache` keyed `testmon-backend-<os>-<sha>`. The cache is *written* only by main-push runs and the nightly `backend-testmon-refresh` job. PR runs *only restore*, so PR-specific fingerprints can't poison the next PR's restore-keys fallback.
- **Staleness bound** — nightly wipes `.testmondata` and re-traces the full backend suite, so a stale fingerprint can survive at most one nightly cycle (≤24 h).
- **Bypass cases**:
  1. **Force-triggered batches** (changed test files / path-triggered files) run unfiltered.
  2. **Fixture data changes** (`backend/tests/fixtures/`) flip the whole job into unfiltered mode via `PT_BACKEND_TESTMON_BYPASS`. Testmon hashes Python source blocks, not data files — JSON/CSV edits would slip past it.
  3. **Cache miss** — testmon runs unfiltered and populates fingerprints for next time.

**Local equivalent.** `pytest --testmon` from `backend/` after `uv sync --extra dev`. The DB at `backend/.testmondata` is local-only and `.gitignore`'d.

### Vitest --changed filter (frontend-test only)

Within the frontend bucket, vitest is invoked with `--changed <base>` so it runs only the tests whose Vite module-graph closure intersects the diff. No cache, no staleness — Vite builds the static ESM import graph fresh on each run.

- **Type-only blind spot.** `import type` references are erased before graph construction, so type-only edits look like a no-op to `--changed`. `tsc --noEmit` and `svelte-check` run unfiltered in the same job and cover this.
- **`fetch-depth: 0`** on the frontend-test checkout — vitest shells out to `git diff`.
- **Edge cases**:
  1. **Empty changed-set** → "No test files found, exiting with code 0". Acceptable: tsc + svelte-check still ran, and the e2e job still runs.
  2. **Test file changed directly** → vitest sees the test itself in the diff and runs it; no special handling.
  3. **Runtime-string dynamic imports** are not in the static graph. Rare in practice; add a path trigger if a real case appears.

**Local equivalent.** `npx vitest run --changed origin/main` from `frontend/`.

### E2e smoke-tier filter (e2e-test only)

E2e runs only the **smoke set** on PRs (`tests/e2e/smoke.spec.ts`). Other specs are nightly-by-default and pulled onto PR only when path-triggered.

- **Pulled onto PR** by `scripts/path_triggers.sh`: changed test files always run, and source-area mappings (e.g. `backend/src/app/routes/` → `items-flow.spec.ts`) bring in their covered specs.
- **Nightly safety net** — `.github/workflows/nightly.yml e2e-slow` runs every spec under `tests/e2e/` unfiltered.

**Local equivalent.** `npx playwright test tests/e2e/smoke.spec.ts` from `frontend/`. Run the full suite (`npx playwright test`) before release-tagging or when reviewing nightly failures.

### Slow tier

On top of the scope triage, the backend and e2e suites apply a **fast / slow split**:

- **Fast tier** runs on every relevant-scope PR:
  - Backend: `pytest -m "not slow"` (skips anything tagged `@pytest.mark.slow`).
  - E2e: the smoke set (selection by file, not marker).
- **Slow tier** runs nightly via `.github/workflows/nightly.yml` (cron `0 3 * * *`), plus on `release: published` and manual `workflow_dispatch`.

Two carve-outs pull nightly-default tests back into a PR's fast tier:

1. **Changed test files always run.** A test you just added or modified runs regardless of marker / smoke-set membership.
2. **Path-triggered tests** for known source ↔ test pairings:

   | Changed source path | Pulls in |
   |---|---|
   | `backend/src/app/main.py` or `backend/src/app/routes/` | backend `tests/test_items.py` + `tests/test_items_integration.py` |
   | `backend/tests/fixtures/` | disables testmon for the whole backend-test job |
   | `backend/src/app/routes/` | e2e `tests/e2e/items-flow.spec.ts` |

   Update both this table AND the `if` blocks in `scripts/path_triggers.sh` when adding triggers — keep them in lock-step.

**Marking a test slow.** Use `@pytest.mark.slow` (backend) when a test has any of: a wall-clock perf assertion tight on shared runners; a full-stack pipeline run on a realistic fixture; cumulative wall-clock > ~5 s where the coverage isn't unique to this test. For e2e: put the spec outside the smoke set (selection is by file).

**Detection latency tradeoff.** A nightly-default test regression caused by a change that *doesn't* path-trigger has up to ~24 h detection latency. Acceptable for genuine perf assertions and feature-specific coverage. If you find a class of regressions slipping past the path-trigger map, add the missing trigger rather than move the test into the fast tier.

## Multi-agent integrity defenses

This template is designed around a specific failure mode: **two or more agents working in parallel on different parts of the codebase, with different context perspectives, neither side's tests failing in isolation**. The CI machinery above isn't optional — it's the safety net. Each layer catches a specific class of conflict:

- **`alembic heads` single-head check** catches sibling migration branches. Two agents that both create migrations off the same parent each produce a passing test run; the merge produces a multi-head DB that won't `upgrade head`. The check runs before pytest in the backend job.
- **`contract_check.py`** catches frontend/backend surface drift. One agent renames an endpoint while another agent's frontend keeps the old name — both sides' unit tests pass, the wired-up flow fails. Runs on every non-docs PR.
- **e2e for single-side PRs** catches the same class of drift at the runtime level. The contract check verifies path-and-method shape; e2e verifies actual behaviour over the wire.
- **`testmon` and `vitest --changed` carve-outs** — fixture-bypass, changed-file-always-run, path-triggered force-include — are there because an aggressive impact filter can miss the cross-cut case where agent A's change should re-run agent B's test but the filter doesn't see the dependency. The carve-outs are the escape hatches.
- **Comment-density check** catches doc-bloat drift. Agents tend to write essays next to one-line fixes; subsequent agents read the closest comment first and design follow-on work around the paraphrase. The check fails the commit when net doc growth exceeds net code growth.

If you find yourself disabling one of these gates, the right move is to fix the cause, not the gate.

## CI gates on main

Branch protection on `main` requires these CI jobs to pass before any merge:

- `CI / backend-test` — ruff check, ruff format --check, mypy strict, `alembic heads` single-head check, `alembic upgrade head` on a fresh Postgres, pytest (fast tier with testmon)
- `CI / frontend-test` — tsc --noEmit, svelte-check, vitest run --changed
- `CI / e2e-test` — boots backend (with migrations applied) + frontend, runs Playwright over the smoke set plus any path-triggered specs
- `CI / contract-check` — verifies every frontend API call has a matching backend route

Direct push to `main` is disabled. All merges go through PRs that pass these gates.

### Debugging a failing CI run

```bash
gh run list --limit 5                                 # recent runs
gh run view <run_id> --log-failed                     # tail of failing steps
gh run view <run_id> --json jobs --jq '.jobs[] | {name, conclusion}'
```

For e2e failures, the workflow uploads `playwright-results` (HTML report + per-failure trace, screenshot, video) on `if: failure()`:

```bash
gh run download <run_id> --name playwright-results --dir /tmp/pw
# then open /tmp/pw/playwright-report/index.html
```

Re-run a failing job after fixing the cause:

```bash
gh run rerun <run_id> --failed
```

## No buggy quick fixes

When a bug is found in production code (on `main`), **do not patch it in place with a quick fix and push.** Branch protection enforces this technically, but the intent is broader:

- **Fix bugs via branches + PRs.** Surface-level fixes often reveal deeper mismatches (different keyword names, missing dependencies, contract disagreements between services) that multiple reactive patches accumulate rather than resolve.
- **When a fix needs 2+ iterations of patch-then-test, stop.** Revert the in-progress work, audit the actual state (backend routes vs frontend calls, function signatures, dependency tree), and come back with a single coherent change.
- **Integration tests are non-negotiable** for fixes that cross the backend/frontend boundary. "All unit tests pass" is not the same as "the feature works end-to-end."
- **Reference prior helpers instead of inventing workarounds.** If a helper already exists, reuse or share it — do not write a new one that is nearly-but-not-quite the same.

## GitHub API: working patterns

The `gh` CLI is the right tool for issues, PRs, labels, and CI status. From inside the repo it infers the repo slug from the `github` remote, so `--repo` is only needed when running outside.

```bash
# View an issue. Pass --json so gh skips the Projects-classic GraphQL
# call that 500s on this repo.
gh issue view 42 --json number,title,state,body,labels,comments

# Create a PR. Use --body-file for non-trivial bodies so shell quoting
# can't truncate.
gh pr create --base main --head feat/x --title "feat(x): ..." --body-file /tmp/pr-body.md

# View a PR (state, mergedAt, statusCheckRollup, files, etc.).
gh pr view 42 --json number,state,mergedAt,statusCheckRollup,headRefName

# Add / remove labels.
gh issue edit 42 --add-label in-progress
gh issue edit 42 --remove-label ready

# CI status for a commit.
gh pr checks 42

# Comment on an issue / PR.
gh issue comment 42 --body-file /tmp/comment.md

# Anything not covered by a subcommand: drop to `gh api`.
gh api repos/<owner>/<repo>/issues --paginate \
  --jq '.[] | select(.pull_request == null) | {number, title, labels: [.labels[].name]}'
```

**Things that do NOT work:**
- `gh issue view <n>` *without* `--json` — triggers a Projects (classic) GraphQL query that returns HTTP 500.
- Embedding tokens in `git push` URLs — exposes them in process listings.

**Robust body pattern for PRs / issues:**

```bash
cat > /tmp/pr-body.md <<'EOF'
## Summary
- bullet one
- bullet two with `code` and **markdown**

## Test plan
- [x] tests pass
EOF
gh pr create --base main --head feat/x --title "feat(x): ..." --body-file /tmp/pr-body.md
rm /tmp/pr-body.md
```

## Model selection for subagents

When spawning subagents via the `Agent` tool, choose the model deliberately. Principle: *spend on reasoning, not on plumbing.*

| Work type | Model | Rationale |
|---|---|---|
| Algorithmically heavy work (numerical methods, novel data structures, complex correctness reasoning) | `opus` | A wrong implementation silently produces wrong output. |
| Production-quality UI with real interaction design | `opus` or `sonnet` | Opus for novel interaction design; sonnet for following existing patterns. |
| Plumbing: Pydantic schemas, REST endpoints, API clients, form scaffolding, test fixtures, file I/O, config | `sonnet` | Mostly pattern-following work. Sonnet is fast, cheap, and competent. |
| Haiku-sized tasks: single-file cleanups, comment additions, simple renames, CI tweaks | `haiku` | Quick deterministic work where speed matters more than reasoning depth. |

Pass the chosen model explicitly: `model: "opus"` / `model: "sonnet"` / `model: "haiku"`. If omitted, the subagent inherits from the parent — usually more expensive than necessary.

## Agent pipeline

Automation runs via `/schedule` in Claude Code — remote Claude agents that execute on a cron schedule, authenticated to GitHub via the `gh` CLI. A sample routine is checked in at `.claude/schedules/issue-poller.md`.

The issue → PR pipeline:

1. Human creates a GitHub issue with labels: `ready` (triggers pickup) plus optionally `model:opus` / `model:sonnet` / `model:haiku` (default: sonnet).
2. A scheduled `/schedule` trigger polls every N minutes for `ready`-labelled issues without `in-progress` or `blocked` labels:
   - Adds `in-progress` via `gh issue edit <n> --add-label in-progress`
   - Spawns a subagent with the chosen model to read CLAUDE.md, implement the fix, open a PR via `gh pr create`
   - Removes `in-progress` on success, adds `failed` on failure
3. CI gates the PR (backend-test, frontend-test, e2e-test, contract-check, alembic heads single-head).
4. A second trigger auto-merges PRs with all checks green (`gh pr merge <n> --squash --delete-branch`) and handles failing PRs by pushing fixes or leaving comments.

Audit-style scheduled runs (weekly drift checks, stale-branch reports) are also good candidates for `/schedule`.
