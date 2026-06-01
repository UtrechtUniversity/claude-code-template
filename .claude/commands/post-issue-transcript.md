---
description: Post a user/Claude conversation transcript as a comment on a GitHub issue — durable audit trail at PR-open / issue-close milestones
argument-hint: "[issue-number] — issue to comment on (defaults to the issue this conversation is closing)"
allowed-tools: ["Bash"]
---

# Post issue transcript

Post a transcript of this conversation as a comment on a GitHub issue, so the
issue itself carries a durable record of the reasoning that produced the
change.  The hook at `.claude/hooks/issue-close-reminder.sh` triggers this
command automatically when an agent merges a PR or closes an issue, but you
can also invoke it on demand.

## When to invoke

- **Auto-trigger:** the `PostToolUse` hook fires after a `gh pr merge` or
  `gh issue close` (or the equivalent `gh api` calls).  When you see the
  system reminder, run this flow.
- **PR-open:** when opening a PR that closes an issue (`Closes #N` in the
  body), post the transcript on `#N` first or alongside the PR.  This keeps
  the verbatim user prompts intact before any auto-compaction.
- **On-demand:** the user says "post transcript to #N" or similar.

Skip if a transcript was already posted in this session.

## Format

For each turn in the conversation, in order:

```markdown
**User:** <user prompt, quoted verbatim — except redact tokens, see below>

**Claude (summary):** <1–3 sentences — what you did, what you found, what
decision you made.  No code blocks, no decision-tree minutiae, just enough
that the next prompt makes sense in context.>
```

If the runtime auto-compacted earlier messages, the "verbatim" prompts may
already be summaries — call this out at the top of the comment so the reader
knows.

### Redact tokens before posting — non-negotiable

Users sometimes paste GitHub PATs or other secrets directly into prompts so
agents can use them in-session.  That is an in-session trust decision;
**posting them as issue comments is not.**  Issue comments are durable,
world-readable on GitHub, and indexed.  A token that lands in a comment is
effectively published.

Before posting, scrub each user-turn for token-like content and replace it
with a placeholder.  Treat as a token any of:

- GitHub PATs (`ghp_…`, `github_pat_…`, hex strings of ~40 chars in a token-shaped context)
- Bearer tokens, API keys, `Authorization:` header values
- AWS / GCP / Anthropic / OpenAI keys (`sk-…`, `AKIA…`, etc.)
- Anything pasted with framing like "here's the token", "use this PAT", "auth:"
- Long opaque strings whose purpose the user described as auth/credential

Replace with `[redacted token]` (or `[redacted GitHub PAT]` when the type is
obvious).  Keep the surrounding prose intact so the conversation still
reads.  When in doubt, redact — there is no cost to a false positive and
the cost of a false negative is a leaked credential.

This applies even if the user's prompt was "post this to the issue" — the
verbatim instruction never overrides the redaction rule.

## Steps

1. **Resolve the issue number.**
   - If `$1` is given, use it.
   - Otherwise look at the PR you just opened/merged and read the
     `Closes #N` line from its body.
   - Otherwise ask the user.

2. **Compose the transcript** in the format above.  Include only the
   conversation that produced the change being shipped — earlier unrelated
   turns can be omitted with a brief note (`*[earlier turns about X
   omitted]*`).

3. **Post via the `gh` CLI:**
   ```bash
   cat > /tmp/transcript.md <<'TRANSCRIPT'
   <markdown body here>
   TRANSCRIPT
   gh issue comment <N> --body-file /tmp/transcript.md
   rm /tmp/transcript.md
   ```
   Always use `--body-file` for the transcript — inline `--body "..."` mangles
   multi-paragraph markdown with backticks and em-dashes.

4. **Confirm** with the issue-comment URL `gh` prints on success.
