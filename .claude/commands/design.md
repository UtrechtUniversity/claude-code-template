---
description: Create a design doc for a new feature from the project template
argument-hint: "<feature-name> — short description of what to design"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Agent"]
---

# Create Design Doc

Create a design doc for a new feature using the project template.

## Steps

1. **Read the template:** Read `docs/design/TEMPLATE.md` for the required structure.

2. **Read existing decisions:** Read `docs/DECISIONS.md` to understand existing patterns and constraints. The new feature must be consistent with settled decisions.

3. **Read the data model:** Read `docs/DATA_MODEL.md` to understand how the feature fits into the existing model.

4. **Ask the user** to describe the feature if not already provided in the argument. Get: what problem it solves, who it's for, and any constraints.

5. **Create the doc:** Write `docs/design/<feature-name>.md` following the template structure:
   - **Problem** — specific, user-centric ("coaches can't X", not "the system should Y")
   - **Proposal** — what changes, how it works, what it touches. No field listings.
   - **Decisions** — new decisions this feature requires. Check for conflicts with existing decisions.
   - **UX** — reference any frontend guideline docs under `docs/` if present; otherwise sketch the shape briefly
   - **Implementation Status** — all items start as "not started"
   - **Open Questions** — anything needing a decision

6. **Record decisions:** For any new decisions identified, add them to `docs/DECISIONS.md` with maturity level `[draft]` and rationale.

## Rules

- Keep it short. If a section exceeds ~20 lines, it's too detailed for a design doc.
- Focus on *what* and *why*. Field-level detail belongs in code.
- Every decision must have a "Why:" rationale.
- Flag any conflict with existing settled decisions — these need explicit user approval to override.
