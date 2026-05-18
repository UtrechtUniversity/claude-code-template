---
description: Check if code changes are consistent with all recorded decisions in DECISIONS.md
allowed-tools: ["Read", "Grep", "Glob", "Bash", "Agent"]
---

# Decision Consistency Audit

Check the current branch's changes against every relevant decision in `docs/DECISIONS.md`.

## Steps

1. **Read all decisions:** Read `docs/DECISIONS.md` in full.

2. **Get the diff:** Run `git diff main...HEAD` to see all changes.

3. **For each changed file, search DECISIONS.md for relevant decisions by topic.** Match by topic, not by decision number. Common topic clusters to consider:

   - **Backend models / persistence** — schema conventions, migration discipline, ORM choices
   - **API / routes** — auth, permissions, error envelope, pagination, naming
   - **Frontend** — component conventions, state management, accessibility
   - **CI / infra** — scope detection, test tiers, branch protection, deployment

   The template seeds `docs/DECISIONS.md` with D1 (stack) and D2 (Alembic). Per-project decisions accumulate from D3 onwards.

4. **Flag three types of issues:**

   **Contradiction** — change directly violates a settled or accepted decision. Must be fixed or the decision explicitly updated with user approval.

   **Gap** — change introduces a new pattern not covered by any existing decision. Suggest recording it.

   **Drift** — change is technically consistent but moves away from the spirit of a decision. Flag for discussion.

5. **Check decision maturity:**
   - Contradicting a `[settled]` decision is a hard block
   - Contradicting an `[accepted]` decision needs user acknowledgement
   - Contradicting a `[draft]` decision is fine — drafts are proposals

## Output format

For each finding:
```
[CONTRADICTION|GAP|DRIFT] <decision title>
File: <path>:<line>
Issue: <what the code does vs what the decision says>
Fix: <suggested remediation>
```

End with a summary: total decisions checked, contradictions, gaps, drifts.
