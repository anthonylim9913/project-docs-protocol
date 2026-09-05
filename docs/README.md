# project-docs-protocol — its own docs

The skill runs the protocol it ships. Bootstrap: read `STATUS.md`, then the last 3–5 `CHANGELOG.md` entries, then skim `DECISIONS.md`. Close: CHANGELOG entry first, then rewrite STATUS, then a DECISIONS entry only if a real alternative was rejected. Doctor: `python3 scripts/docs-doctor.py .` on demand or after a red flag. Brief: CHANGELOG entry, then DECISIONS, then STATUS — DECISIONS before the rewrite removes the question. Formats are the ones in `../templates/README.md`.

The audit that produced the current state is private; its population-level findings are in `EVIDENCE.md`, and its recommendations are tracked in `STATUS.md` (Next / Deferred) as they are worked, not as a separate roadmap.

*Installed via the `project-docs-protocol` skill — on itself.*
