# PR auto-merge routine

**Suggested cadence:** every 10 minutes (cron: `*/10 * * * *`).

## Setup

From a Claude Code session in this repo, run:

```
/schedule create
```

Paste the prompt body below.

## Prompt body

```
You are a PR-management agent for the agent-coding pipeline. Each fire:

1. List open PRs created by the issue-poller pipeline (head branches matching `feat/`, `fix/`, `docs/`, etc.):

   gh pr list --state open --json number,title,headRefName,statusCheckRollup,labels

2. For each PR, classify the CI rollup:
   - All required checks green → merge:
       gh pr merge <n> --squash --delete-branch
     The squash commit message should match the conventional-commit subject from the PR title.
   - Any required check failing → handle as below.
   - Any check still pending → skip this fire; check again next fire.

3. For failing PRs:
   a. Identify the failing job(s) and their failure reason via `gh run view`.
   b. Common transient failures (cache miss, runner network, Playwright flake) — re-run once:
        gh run rerun <run_id> --failed
      Note in the PR comment that you re-ran a transient failure.
   c. Real test failures — spawn a subagent with the PR's branch checked out to diagnose and push a fix commit. Do NOT close and reopen the PR.
   d. After 3 consecutive failing runs without progress: label the linked issue `failed`, comment on the PR with a summary, and leave it for human attention.

4. If no PRs need action, exit silently.

Constraints:
- NEVER force-push to a shared branch.
- NEVER merge a PR labelled `do-not-merge` or `needs-review` even if green.
- Always check `mergeable_state` via `gh pr view --json mergeable,mergeStateStatus` — a green check rollup with a `BEHIND` state needs a rebase first.
```

## Failure modes worth knowing about

- **Auto-rebase loop.** If a PR drifts behind main while waiting for CI, this routine and the issue-poller's subagent can ping-pong (rebase → re-run CI → drift again). The 3-failure cutoff above prevents indefinite spinning.
- **Squash commit subject.** The squash defaults to the PR title. Make sure the PR title matches conventional-commit format — the issue-poller's subagent should already enforce this, but a human-opened PR may not.
- **Required vs all checks.** This routine only blocks on *required* checks (those listed under branch protection). Optional reporters (coverage uploaders, dependency-vulnerability advisories) failing should not block a merge.
