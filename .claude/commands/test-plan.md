---
description: Generate test scenarios for a feature or change
argument-hint: "<feature or file> — what to generate tests for"
allowed-tools: ["Read", "Grep", "Glob", "Bash", "Agent"]
---

# Generate Test Plan

Create test scenarios for a feature or code change, covering happy paths, edge cases, and integration points.

## Steps

1. **Understand the change:** Read the files or feature description provided. If a design doc exists in `docs/design/`, read it.

2. **Read relevant decisions:** Check `docs/DECISIONS.md` for decisions that affect testing.

3. **Identify test layers:**

   **Backend unit tests** — for pure business logic (validation, transformations, domain rules):
   - Happy path for each operation
   - Edge cases specific to the domain
   - Validation failures (bad input, missing required fields)
   - Permission checks (unauthenticated, wrong role) where the project uses auth

   **Backend integration tests** — for API endpoints:
   - Request/response shape per the contract
   - Database round-trips for write endpoints
   - Cross-model effects (cascading deletes, derived columns, materialised views)
   - Mark long-running ones with `@pytest.mark.slow`

   **Frontend tests** — for components and hooks:
   - Component rendering with different states (loading, data, empty, error)
   - User interactions (clicks, keyboard shortcuts, form submission)
   - Accessibility (landmarks, ARIA, keyboard navigation)

   **E2e tests** — for the wired-up flow:
   - Smoke set: app loads, top-level surface is reachable, health endpoint OK
   - Path-triggered: full user journeys exercising the area under change

5. **Write the test plan** as a checklist:

   ```
   ## <Feature Name> Test Plan

   ### Unit Tests
   - [ ] <test description> — <what it verifies>

   ### Integration Tests
   - [ ] <test description> — <what it verifies>

   ### Frontend Tests
   - [ ] <test description> — <what it verifies>

   ### Edge Cases
   - [ ] <test description> — <what it verifies>
   ```

6. **Flag gaps:** If existing code related to this feature has no tests, note it.

## Rules

- Test behaviour, not implementation. Assert outcomes via API responses and GraphQL reads.
- Mock only at I/O boundaries (external APIs, email, push notifications). Never mock internal methods.
- Every test should have a clear "what it verifies" description.
- Reference specific decisions where they drive test expectations (e.g., "per D15, wide runs should not appear in batter stats").
