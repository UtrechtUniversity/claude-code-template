# Issue poller routine

**Suggested cadence:** every 10 minutes during work hours (cron: `*/10 8-22 * * 1-5`).

**Required labels:** `ready`, `in-progress`, `blocked`, `failed`, `model:opus`, `model:sonnet`, `model:haiku`.

## Setup

From a Claude Code session in this repo, run:

```
/schedule create
```

Paste the prompt body below when asked, and pick the suggested cadence.

## Prompt body

```
You are a polling agent for the agent-coding pipeline. Each fire:

1. List `ready`-labelled issues that are NOT also labelled `in-progress`, `blocked`, `failed`, `wontfix`, `duplicate`, or `invalid`:

   gh issue list --label ready --state open --json number,title,labels --jq \
     '.[] | select(.labels | map(.name) | (contains(["in-progress"]) or contains(["blocked"]) or contains(["failed"]) or contains(["wontfix"]) or contains(["duplicate"]) or contains(["invalid"]))| not) | {number, title, labels: [.labels[].name]}'

2. For each unlabelled ready issue (process one per fire — don't batch in parallel):

   a. Mark it in progress and clear the pickup flag:
        gh issue edit <n> --add-label in-progress --remove-label ready

   b. Determine the model from a `model:<name>` label if present; default to sonnet.

   c. Spawn a subagent with that model and a self-contained brief:
        - Read CLAUDE.md
        - Read the issue body and any referenced design docs
        - Implement the change following the Git workflow in CLAUDE.md
        - Open a PR via `gh pr create` once local tests pass for the change scope

   d. On subagent success: leave `in-progress` on the issue — CI gates and the PR-merge routine handle the rest.

   e. On subagent failure: replace `in-progress` with `failed` and leave a comment summarising what blocked it.

3. If no ready issues exist, exit silently.

Constraints:
- Do not pick up issues whose body explicitly says "needs human" or whose labels include `needs-decision` — surface these to the user (you can comment on the issue) but do not act.
- Do not touch labels you didn't add (`wontfix`, `priority:*`, etc.).
- One issue per fire keeps a buggy subagent from racing through the backlog.
```

## Failure modes worth knowing about

- **Auth expired.** `gh auth status` will fail; the routine will silently no-op (no issues "found"). The pipeline goes quiet but doesn't surface the cause. Manually run `gh auth status` if the queue stops draining.
- **Label drift.** If someone manually adds the `in-progress` label without the routine seeing it, the issue won't be picked up — by design (it's already being worked on). If the label gets stuck on a closed issue, just remove it.
- **Concurrent ready issues.** "One per fire" is deliberate. A 10-minute cadence drains 6 issues per hour, which matches the rate at which agents can realistically finish small changes.
