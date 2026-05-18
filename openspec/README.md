# OpenSpec

Spec-driven workflow for describing capabilities before implementing them.

- `specs/<capability>/spec.md` — the authoritative capability contract. REQ-* identifiers live here.
- `changes/<change-id>/` — proposals in flight (design, tasks, affected specs). Archived once implemented.

Use the `/opsx:propose`, `/opsx:explore`, `/opsx:apply`, and `/opsx:archive` slash commands to drive the lifecycle.
