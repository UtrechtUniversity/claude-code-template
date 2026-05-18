---
description: Pre-PR review — check changes against project guidelines (decisions, data model, UX, security, tests)
allowed-tools: ["Read", "Glob", "Grep", "Bash", "Agent"]
---

# Pre-PR Review

Review the current branch's changes against project guidelines. Focus on design judgment — mechanical checks (formatting, tokens, secrets) are enforced by pre-commit hooks and CI.

## Steps

1. **Get the diff:** Run `git diff main...HEAD` to see all changes in this branch.

2. **Decision consistency** (`docs/DECISIONS.md`):
   - Read the decision log
   - For each changed file, check if any decision is relevant
   - Flag changes that contradict settled or accepted decisions
   - Flag new patterns not covered by existing decisions — suggest recording them
   - For a thorough audit, run `/audit-decisions`

3. **Data model consistency** (only if `docs/DATA_MODEL.md` exists in the project):
   - If any backend model is added/changed, verify consistency with the data model doc
   - Flag new models or fields not reflected in the doc

4. **Frontend UX** (only if a frontend UX guideline doc exists under `docs/`):
   - Check component conventions: empty states, error handling, accessibility
   - Check responsive behaviour at documented breakpoints

5. **Schema migrations** (if backend models changed):
   - Verify an Alembic revision was added (`backend/alembic/versions/`)
   - Verify `alembic heads` returns a single head — multi-head means a parallel branch needs resolving
   - For a thorough check, run `/audit-decisions` against D2

6. **Security**:
   - Check new endpoints have explicit auth / permission guards if the project uses them
   - Check user input goes through Pydantic validation, not raw `request.json()`
   - Check for injection risks (SQL via raw queries, XSS, command)
   - Check auth tokens are not logged or exposed in URLs
   - For a thorough audit, run `/audit-security`

6. **Testing**:
   - Check if new code has corresponding tests
   - Check if changed code's existing tests still make sense
   - Flag untested edge cases

## Output format

For each area, report one of:
- **PASS** — no issues found
- **WARN** — minor issues or suggestions
- **FAIL** — violations that must be fixed before merge

List specific file:line references for every issue found.

**PR body template:**
When this review passes and a PR is created, use: `## Summary` with bullet points, `Closes #<issue>` for GitHub auto-close linkage, and `## Test plan` with checkboxes.
