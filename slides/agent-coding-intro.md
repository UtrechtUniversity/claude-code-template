---
marp: true
theme: uu
paginate: true
header: "Coding with AI agents on real systems"
---

<!-- _class: title -->
<!-- _paginate: false -->
<!-- _header: "" -->

<!--
SKELETON — fill in detail when preparing.
Preview live: install the "Marp for VS Code" extension, open this file,
"Marp: Toggle Marp Feature" + open preview side-by-side.
Export:  marp slides/agent-coding-intro.md --pdf
         marp slides/agent-coding-intro.md --html
-->

# Coding with AI agents on real systems

### What happens when multi agents fight over one codebase

<!--
HOOK: the multi-agent failure mode.
- Two agents, two PRs, both pass their own tests
- Neither sees the other's change
- Both merge clean. main breaks.
That failure mode drives every defense in this talk.
-->

---

## 1. Docs are the contract with agents

- Agents read CLAUDE.md, READMEs, comments **at the start of every session**
- If you let agents *write* docs unchecked, the docs drift into agent-flavoured prose
- Successor agents read paraphrased prose, design follow-on work around the paraphrase
- **Read carefully. Edit deliberately. Treat docs like code.**

<!--
"Garbage in, garbage out" beat.
Concrete example: the comment-density pre-commit hook in this repo exists
because agents (especially Opus) write essays next to one-line fixes.
-->

---

<style scoped>
blockquote { font-size: 2.2em; font-style: italic; border: none; text-align: center; margin-top: 1.5em; }
.tooling { font-size: 0.75em; color: #666; margin-top: 3em; }
</style>

> "Markdown is the new normal"

<div class="tooling">

Tooling: VS Code · *Markdown All in One* · *Markdown Preview Enhanced* · *Marp* (these slides)

</div>

---

## 2. Capture the *why*, not just the *what*

- **DECISIONS.md** — every non-trivial choice: status, context, decision, **rejected alternatives**
- **`/design <feature>`** — design doc before coding; captures what you *didn't* build
- **OpenSpec / `/opsx:propose`** — capability-level specs with REQ-* identifiers
- The diff carries the *what*. Successor agents inherit the file system, not the conversation.

<!--
The rejected-alternatives part is crucial. Without it, the next agent will revisit
the same questions you already answered, often arriving at a different conclusion.
-->

---

## 3. Issue ⇄ PR ⇄ Agent — strive for 1:1

| One Issue        | One PR                | One Agent session     |
|------------------|-----------------------|-----------------------|
| Focused task     | One logical change    | Bounded context       |
| Acceptance criteria | Squash-merged       | Self-contained brief  |

**Why it matters:** reviewable diffs, bounded agent context, clean audit trail (issue → PR → commit → branch deleted).

It's a goal, not religion. Real work spills sometimes.

<!--
Slide for tgit intro. Quick glossary if needed:
- branch: a workspace
- commit: a snapshot
- PR: a proposed change, reviewed before merging
- issue: a unit of work, can be assigned a label and picked up
The 1:1 ideal keeps everything traceable and keeps agent context windows small.
-->

---

## 4. CI is the multi-agent safety net

Concrete defenses shipped in this template:

- **`alembic heads`** — single-head check catches *sibling migration branches*
- **`contract_check.py`** — frontend/backend route drift (agent A renames endpoint, agent B's frontend doesn't know)
- **`e2e-test` runs on single-side PRs** — integration is the cross-cut case
- **Comment-density gate** — pre-commit hook that fails when doc growth outpaces code growth

What passes in isolation can still break main. CI is the gate that catches it.

<!--
The comment-density gate is the most concrete "we built this *because* of agents" example.
Walk through one of the defenses if there's time — alembic single-head is the clearest demo.
-->

---

## 5. CI has real costs — mitigate, don't disable

**Cons**
- Slows dev loop (PR-to-merge wall-clock)
- Runner minutes cost real money

**Mitigations** (this template ships all of them)
- **Scope detection** — single-side PRs skip the other side's suite
- **testmon** — backend tests deselected when their Python deps haven't changed
- **vitest `--changed`** — frontend tests run only when their module graph intersects the diff
- **Smoke vs slow tier + path triggers** — heavy e2e nightly; pulled onto PR when relevant

Typical small PR: < 2 minutes instead of > 10. Cost down ~5x.

<!--
The temptation under cost pressure is to drop CI. The right move is to *scope* it.
This slide answers the "we can't afford full CI on every PR" objection directly.
-->

---

## 6. Mechanics: where the levers are

- **`.claude/skills/`** — reusable capabilities. OpenSpec workflow ships here.
- **`.claude/commands/*.md`** — slash commands. `/review`, `/design`, `/ticket`, `/audit-decisions`.
- **Subagents** — spawn one to handle plumbing. Parent keeps the reasoning thread.
- **Model selection** — opus, sonnet, haiku.
  - Opus: when wrong is silent (math, novel algorithms, hairy refactors)
  - Sonnet: pattern-following plumbing — Pydantic schemas, REST endpoints, fixtures
  - Haiku: cleanups, renames, single-file edits

Opus-for-everything is expensive and often slower than sonnet would have been.

<!--
Most people leave everything on Opus by default. A typical agent task is 60% plumbing;
sonnet handles that for about 1/5 the cost without quality loss. The trick is knowing
which task is which, which leads to the next slide.
-->

---

## 7. Roles and personas

Two ways to frame *which* agent shows up.

**Roles** — what job it's doing
- junior dev — needs a brief, asks before guessing
- engineering manager — breaks work into issues, doesn't write code
- system architect — proposes design, surfaces tradeoffs
- code reviewer — reads diffs critically, pushes back
- code cleaner — comments, naming, dead code, low-risk

**Personas** — how it thinks
- meticulous — cross-checks, slow, thorough
- creative — proposes options you didn't list
- **Maverick** — contrarian, breaks the unstated assumption

Roles and personas combine. A *meticulous code reviewer* catches the off-by-one. A *Maverick code reviewer* asks if you should be doing this at all.

<!--
Roles ≠ personas. Roles answer "what is this agent doing?";
personas answer "how does this agent think?". Both shape the system prompt.
Worth picking deliberately, especially when you're going to spawn the agent
autonomously and won't be there to redirect it.

Maverick: not stored as a memory in this repo yet. Worth saving one if I keep
using it — the prompt should describe it once and reuse, not reinvent each time.
-->

---

## 8. Memory and audit trails

What did the agent actually think six months ago?

- **Conversations are ephemeral. Issues live forever.**
- This template includes:
  - `post-issue-transcript` skill — turns conversation into issue comment
  - `issue-close-reminder.sh` hook — fires on `gh pr merge` / `gh issue close`
  - Memory at `~/.claude/projects/<project>/memory/` — facts that survive sessions

Every closed issue carries the reasoning that produced the change.

<!--
This matters most for the "why did we do this?" question that surfaces months later,
or when a new colleague joins and needs to understand the codebase history.
-->

---

## 9. Supervised autonomy, not autopilot

- **`/schedule`** runs Claude on cron — polls for `ready`-labelled issues, picks them up
- Sample routines in `.claude/schedules/`:
  - issue-poller · pr-auto-merge · stale-branch-sweep
- **Humans choose the work** (the `ready` label, model selection)
- **Humans approve the merge** (auto-merge on green, or manual review)
- **Agents do the typing. Not the deciding.**

<!--
Close on this. For the shallow-git crowd, "agent pipeline" can sound like autopilot.
The autonomy is bounded by labels in and reviews out. The humans never leave the loop;
they just stop being the bottleneck on routine work.
-->
