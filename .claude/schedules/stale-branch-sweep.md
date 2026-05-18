# Stale branch sweep routine

**Suggested cadence:** weekly, Monday morning (cron: `0 9 * * 1`).

## Setup

From a Claude Code session in this repo, run:

```
/schedule create
```

Paste the prompt body below.

## Prompt body

```
You are a hygiene agent for the agent-coding pipeline. Each fire (weekly):

1. List remote branches with no commits in the last 14 days:

   git fetch --prune
   for ref in $(git for-each-ref --format='%(refname:short)' refs/remotes/origin/); do
     last=$(git log -1 --format=%cs "$ref" 2>/dev/null || echo "?")
     echo "$last $ref"
   done | sort

2. For each branch older than 14 days that isn't `main`:
   - Check if there's an associated PR (open or closed):
       gh pr list --state all --head <branch-name>
   - If the PR is merged or closed: candidate for deletion.
   - If the PR is open and stale: leave it; comment-ping is the human's call.
   - If no PR exists: candidate for deletion.

3. Open an issue listing the deletion candidates. Do NOT auto-delete — branch
   deletion is destructive enough to warrant a human signoff. Title:
   "Weekly stale-branch sweep — N candidates".

Constraints:
- Do not touch branches whose names start with `release/` or `hotfix/`.
- Do not touch branches that have only just had their PRs closed (< 7 days ago) —
  the author may want to revive.
```

## Failure modes worth knowing about

- **Local clone drift.** If the host running `/schedule` has a stale local clone, `git for-each-ref` will list branches that no longer exist on the remote. The `git fetch --prune` at the start of the prompt handles this — keep it.
- **Forks / dependabot branches.** If you accept PRs from forks, this routine will only see branches in the canonical remote; fork branches are dependabot/renovate's concern.
