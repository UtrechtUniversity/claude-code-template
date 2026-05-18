# Sample schedule configurations

This directory contains sample routines for the `/schedule` slash command — they describe what to paste into `/schedule` when setting up the agent automation pipeline.

The routines themselves are not auto-loaded; `/schedule` stores them externally to the repo. These files are templates and documentation for the agent-pipeline mechanics described in `CLAUDE.md` → "Agent pipeline".

## Routines

| File | Cadence | Purpose |
|---|---|---|
| [`issue-poller.md`](issue-poller.md) | every 10 min during work hours | pick up `ready`-labelled issues, spawn an implementation subagent |
| [`pr-auto-merge.md`](pr-auto-merge.md) | every 10 min | merge PRs with all CI green; comment / re-run / push fixes on failing PRs |
| [`stale-branch-sweep.md`](stale-branch-sweep.md) | weekly | report branches with no activity for 14 days |

## Setup

1. Authenticate the `gh` CLI on the host running `/schedule` (`gh auth login --scopes "repo,read:org"`).
2. Create the repo labels the routines depend on: `ready`, `in-progress`, `blocked`, `failed`, `model:opus`, `model:sonnet`, `model:haiku`.
   ```bash
   for L in ready in-progress blocked failed; do
     gh label create "$L" --color ededed --description "agent pipeline label" || true
   done
   for M in opus sonnet haiku; do
     gh label create "model:$M" --color cccccc --description "agent model selection" || true
   done
   ```
3. Invoke `/schedule` from Claude Code with the prompt body from one of the files below.

## Why these are checked in

Two reasons:

- **Reproducibility.** Anyone setting up the pipeline starts from the same routine prompts; differences between deployments are intentional, not setup drift.
- **Reviewability.** Routine prompts are agent instructions — they belong under version control alongside the code they automate. When something goes wrong on the pipeline, the routine prompt is part of the audit trail.
