---
description: Security audit of code changes — OWASP top 10, auth, permissions, data exposure
allowed-tools: ["Read", "Grep", "Glob", "Bash", "Agent"]
---

# Security Audit

Audit the current branch's changes for security issues. Secrets and `.env` files are blocked by pre-commit hooks — this audit focuses on logic-level security against the FastAPI + SQLAlchemy + Svelte stack.

## Steps

1. **Get the diff:** Run `git diff main...HEAD` to see all changes.

2. **Read auth and security decisions:** Search `docs/DECISIONS.md` for decisions related to authentication, authorisation, tokens, permissions, data exposure, and rate limiting. Read each relevant decision in full.

3. **Check each category:**

### Authentication & Authorisation
- New routes must have an explicit auth dependency if the project uses authentication. Public endpoints should be conspicuous, not the default.
- Token handling follows the project's pattern (cookie / Authorization header / OAuth). No tokens in query parameters or logged at INFO level.
- WebSocket / SSE auth happens before any data is exchanged.
- Bear context headers (tenant, organisation, locale) must not double as authorisation — they are *context*, not credentials.

### Input Validation
- All user input goes through Pydantic validation. No raw `request.json()` or untyped `body=...` parameters.
- No string formatting with user input into SQL (use SQLAlchemy parameter binding) or shell commands.
- No `{@html foo}` in Svelte or `dangerouslySetInnerHTML` equivalents without sanitisation.
- File uploads are bounded in size and type.

### Data Exposure
- API responses return minimal `*Read` schemas — no accidental ORM-object leak. Check Pydantic `response_model=` is set on every route.
- Error responses do not expose stack traces, SQL, or internal paths in production.
- IDs that allow enumeration (sequential integers) are acceptable for non-sensitive resources; sensitive resources use UUIDs or signed tokens.

### SQL & Migrations
- No raw SQL with f-strings. Use SQLAlchemy expression language or parameter binding.
- Alembic migrations do not introduce destructive operations (DROP COLUMN, DROP TABLE) without a documented data-preservation plan.
- `alembic heads` is single. Multi-head means a parallel migration branch — fix before merge.

### Secrets & Credentials
Pre-commit hooks block hardcoded secrets and `.env` files. Check for subtler issues:
- Secrets passed via URL query parameters or path segments.
- Auth tokens or DB connection strings logged at any level.
- Sensitive data in error responses or in client-visible state (e.g. baked into HTML for hydration).

### Dependencies
- No known-vulnerable packages added (check `gh api /repos/{owner}/{repo}/dependabot/alerts` or run `npm audit` / `pip-audit`).
- No unnecessary new dependencies with broad access (network, filesystem) when stdlib would do.

## Output format

Report findings as:
- **CRITICAL** — must fix before merge (data exposure, auth bypass, injection)
- **HIGH** — should fix before merge (missing permission check, weak validation)
- **MEDIUM** — fix soon (information disclosure, missing rate limiting)
- **LOW** — improve when touching this area (hardening, best practices)

Include file:line references and specific remediation for each finding.
