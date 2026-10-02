# Protocol map

This repository ships the `project-docs-protocol` skill and two optional
companions under `staging/`: `research-protocol` and `architect-protocol`. The
core register is `docs/STATUS.md`, `docs/CHANGELOG.md`, `docs/DECISIONS.md` and,
where adopted, `docs/LEDGER.md`. No companion creates a competing STATUS or
writes those files out of the core order. A project's optional
`SKILL-REGISTRY.md` records the skills it has vendored; it records authority and
never grants it.

How the parts combine — the Bootstrap read order, the companions' Brief and
Close hooks, the registry's authority rules, and which checker to run when — is
specified once, in `SKILL.md`: Install step 1, Bootstrap steps 6–7, and
*Optional companions*. Architect stages additionally use an isolated branch or
worktree, a clean exact subject, complete input hashes and an independent
read-only reviewer (`staging/architect-protocol/SCHEMA.md`).

Core installations need only README, STATUS, CHANGELOG and DECISIONS plus agent
wiring; no registry or companion is required.
