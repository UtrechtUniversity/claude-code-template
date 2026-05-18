---
description: Write a well-structured GitHub issue (bug report or feature request) and create it via the API
argument-hint: "<description> — describe the bug or feature"
allowed-tools: ["Read", "Bash", "Grep", "Glob", "Agent"]
---

# Create GitHub Issue

Write a structured issue and create it via the GitHub REST API (or `gh` CLI if available).

## Steps

1. **Determine issue type** from the user's description: `bug`, `feature`, or `task`.

2. **For bugs**, gather:
   - Steps to reproduce
   - Expected vs actual behaviour
   - Which page/component is affected
   - Ask the user for anything unclear

3. **For features**, check:
   - Read `docs/DECISIONS.md` — does this conflict with any existing decision?
   - If the feature is non-trivial, suggest creating a design doc first (`/design`)

4. **Write the issue** with this structure:

   ```
   ## Description
   <1-2 sentences: what's wrong or what's needed>

   ## Steps to Reproduce (bugs only)
   1. ...
   2. ...

   ## Expected Behaviour
   <what should happen>

   ## Actual Behaviour (bugs only)
   <what happens instead>

   ## Affected Area
   <page, component, API endpoint, or model>

   ## Relevant Decisions
   <list any DECISIONS.md entries that apply, e.g. "D2: Alembic owns the schema">

   ## Acceptance Criteria
   - [ ] <concrete, testable criteria>
   ```

5. **Create the issue** via the `gh` CLI (already authenticated on dev machines — see CLAUDE.md "GitHub API: working patterns").

   ```bash
   # Write the body to a tempfile so multi-line markdown survives shell quoting.
   cat > /tmp/issue-body.md <<'EOF'
   <markdown body here>
   EOF
   gh issue create \
     --title "..." \
     --body-file /tmp/issue-body.md \
     --label ready --label model:sonnet
   rm /tmp/issue-body.md
   ```

   `gh` takes label *names* (not IDs). Labels must exist on the repo first — create once
   with `gh label create <name> --description "..." --color "ededed"`.

   **Formatting rules:**
   - Always use `--body-file` for non-trivial markdown (multi-paragraph, backticks, em-dashes) — inline `--body "..."` gets mangled by shell quoting
   - The body must render correctly as GitHub-flavoured markdown

   **Required labels for agent pickup** (see the Agent Pipeline section of `CLAUDE.md`):
   - `ready` — triggers the `/schedule`-based polling implementer
   - `model:opus` / `model:sonnet` / `model:haiku` — chooses which Claude model implements it (default: `sonnet`)
   - Optionally `blocked` or a `WIP:` title prefix to keep it out of the queue

6. **Return the issue URL** to the user.
