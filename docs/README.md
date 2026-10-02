# project-docs-protocol — its own docs

The skill runs the protocol it ships. Bootstrap: read `STATUS.md`, then the last 3–5 `CHANGELOG.md` entries, then skim `DECISIONS.md`, followed by live `LEDGER.md` rows and conditional `SKILL-REGISTRY.md` routing when installed. Match its trigger and workflow stage, read its capability contract and follow the authorization and unavailable-capability rules in AGENTS/CLAUDE. Close: CHANGELOG entry first, then LEDGER updates and STATUS rewrite, then a DECISIONS entry only if a real alternative was rejected. Doctor: `python3 scripts/docs-doctor.py .` on demand or after a red flag. Brief: CHANGELOG entry, then reserved DECISIONS IDs, LEDGER updates, and STATUS. Formats are the ones in `../templates/README.md`.

The audit that produced the current state is private; its dated, one-machine population summary is anonymised in `EVIDENCE.md`. The repository contains replayable public fixtures; private review artifacts are not acceptance dependencies. Recommendations are tracked in `STATUS.md` and `LEDGER.md` as they are worked.

*Installed via the `project-docs-protocol` skill — on itself.*

Migration workflow: [MIGRATION.md](MIGRATION.md). Executable acceptance and its boundaries: [../tests/README.md](../tests/README.md). Local hardening review: [HARDENING-REVIEW.md](HARDENING-REVIEW.md).

The optional [SKILL-REGISTRY.md](SKILL-REGISTRY.md) records the staged
`research-protocol` and `architect-protocol` companions and is
checked independently from the project root with
`python3 scripts/skill-registry.py .`. It is an inventory only; this file does
not install or activate a skill.

Only the primary session writes this register. Parallel implementation lanes own disjoint source/test files and return findings to that writer; they do not allocate IDs or edit these registers. No other project register owns this repository work.
