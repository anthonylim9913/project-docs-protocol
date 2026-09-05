# STATUS

*Snapshot of where the work is right now. Rewrite this file at each close — never append to it. Keep it around ~40 lines and never over ~60. Past-tense content belongs in CHANGELOG.md, not here.*

*Last updated: 2026-09-06*

## Current phase

**v0.3.0 released — `main` is tagged `v0.3.0` and public; five modes, Doctor 1.3.0**

The branch was hardened against an independent second-model review (17 findings, all reproduced first) and verified by three fresh reviewers before merging. The register that loads for Claude and, through the symlink, for Codex is now the five-mode skill.

## In flight

| Item | Owner | Target | Notes |
|---|---|---|---|
| LEDGER (item-keyed tracker for long finding lists) as a `v0.4.0` candidate | agent | review branch, local, not pushed | Template + SKILL inserts + Doctor rows designed and twice verified; a third review found stale public figures and a stale migration base to fix before it becomes a branch |

## Blocked

*No items.*

## Deferred

| Item | Deferred to | Reason |
|---|---|---|
| Compaction procedure in Mode 3 | after a dry run on the largest retired register | Only one compaction has ever happened; write the procedure from that instance, not from theory (D-0005) |
| Offer bullet for Brief in the wiring block | the next block revision | Would make six freshly re-synced blocks stale (D-0009) |
| Moving the Doctor table and Brief failure modes out of SKILL.md into reference files | when SKILL.md passes ~400 lines | The reviewer's length note is fair (330 lines), but every section is normative or cited; splitting now trades one bootstrap read for two |
| Re-syncing the six externally wired roots for the precedence wording and the examples parenthetical | their next Close | Wording-only drift; the doctor's clause check keys on the clause markers, which are unchanged |

## Next

1. LEDGER `v0.4.0` candidate: apply the third review (Tags column, `extends D-XXXX` form, corrected figures, script-first migration), verify, land on a local branch for owner review.
2. Compaction dry run (separate long-running session; prompt handed over).
3. Run Doctor across the population after the next round of installs and compare with the 2026-09-06 sweep (2 / 7 / 17).

## Open questions (owner)

*None open.*

*Bootstrap reminder: this is the first file to read each session. Close reminder: rewrite it AFTER the CHANGELOG entry — completed items out, new items in, past tense deleted.*
