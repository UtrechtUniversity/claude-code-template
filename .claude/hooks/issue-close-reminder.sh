#!/usr/bin/env bash
# PostToolUse hook for the Bash tool.  Reads the JSON event on stdin.
#
# When the Bash command merged a PR or closed an issue on GitHub
# (either via the `gh` CLI or a direct `gh api` call), emit a system
# reminder telling the agent to post a user/Claude transcript on the
# linked issue, per `.claude/commands/post-issue-transcript.md`.
# Exit 2 routes stderr back into Claude's context as feedback
# (non-blocking — the tool has already run).

set -euo pipefail

# Read the entire payload once so we can pull both ``tool_input.command``
# and ``session_id`` from it (jq consumes stdin).
payload=$(cat)
cmd=$(printf '%s' "$payload" | jq -r '.tool_input.command // empty')
[ -z "$cmd" ] && exit 0

# Avoid self-triggering when the command edits, reads, or smoke-tests
# this hook script (which contains the same patterns we match on).
if printf '%s' "$cmd" | grep -q 'issue-close-reminder.sh'; then
  exit 0
fi

is_merge=0
is_close=0

# `gh pr merge <N>` (with optional flags like --squash --delete-branch).
if printf '%s' "$cmd" | grep -qE '\bgh[[:space:]]+pr[[:space:]]+merge\b'; then
  is_merge=1
fi

# `gh api .../pulls/{N}/merge` — same effect via raw API.
if printf '%s' "$cmd" | grep -qE 'gh[[:space:]]+api[[:space:]].*repos/[^/[:space:]]+/[^/[:space:]]+/pulls/[0-9]+/merge'; then
  is_merge=1
fi

# `gh issue close <N>`.
if printf '%s' "$cmd" | grep -qE '\bgh[[:space:]]+issue[[:space:]]+close\b'; then
  is_close=1
fi

# `gh api ... issues/{N} ... state=closed` — explicit state PATCH.
if printf '%s' "$cmd" | grep -qE 'gh[[:space:]]+api[[:space:]].*repos/[^/[:space:]]+/[^/[:space:]]+/issues/[0-9]+([^/]|$)' \
   && printf '%s' "$cmd" | grep -qE 'state=closed|"state"[[:space:]]*:[[:space:]]*"closed"'; then
  is_close=1
fi

[ "$is_merge" -eq 0 ] && [ "$is_close" -eq 0 ] && exit 0

# Dedupe back-to-back reminders for the same close flow.  A squash-
# merge that auto-closes the linked issue plus a follow-up explicit
# `gh issue close` both fire the hook within seconds; we only want
# one reminder per logical resolution.  Marker is keyed by Claude
# Code session_id so concurrent sessions don't suppress each other.
# ``COOLDOWN_SEC`` is long enough to span a typical merge→close
# pair (seconds) but short enough that genuinely closing a
# *different* issue later in the same session still triggers a fresh
# reminder.
session_id=$(printf '%s' "$payload" | jq -r '.session_id // empty')
marker="/tmp/claude-issue-transcript-fired-${session_id:-default}"
COOLDOWN_SEC=300
if [ -f "$marker" ]; then
  now=$(date +%s)
  mtime=$(stat -c %Y "$marker" 2>/dev/null || echo 0)
  age=$((now - mtime))
  if [ "$age" -lt "$COOLDOWN_SEC" ]; then
    exit 0
  fi
fi

if [ "$is_merge" -eq 1 ]; then
  trigger="merged a PR"
else
  trigger="closed an issue"
fi

touch "$marker"

cat >&2 <<EOF
You just $trigger via the gh CLI.  Per .claude/commands/post-issue-transcript.md,
post a transcript as a comment on the linked issue before declaring the task
done — unless one was already posted in this session.

  gh issue comment <N> --body-file /tmp/transcript.md

Format: \`**User:** <verbatim>\` and \`**Claude (summary):** <1–3 sentences>\` per turn.
See the slash command file for the full spec.
EOF

exit 2
