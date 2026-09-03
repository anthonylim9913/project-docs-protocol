# STATUS

*Snapshot of where the work is right now. Rewrite this file at each close — never append to it. Keep it around ~40 lines and never over ~60. Past-tense content belongs in CHANGELOG.md, not here.*

*Last updated: 2026-09-04*

## Current phase

**v0.3.0 candidate on branch `v0.3.0`, awaiting owner review; `main` is the public `v0.2.0`**

Doctor (Mode 4) and Brief (Mode 5) are integrated on the branch with their template touches, a worked brief, and README paragraphs. Both passed a second adversarial verification round; the eleven remaining minor findings were applied and re-tested against the 25-root census and a 36-fixture break suite. The branch is pushed for review and is not merged.

## In flight

| Item | Owner | Target | Notes |
|---|---|---|---|
| Review and merge `v0.3.0`, then tag | owner | next session | `git diff v0.2.0..v0.3.0`; Doctor exits 0 on this repository |

## Blocked

*No items.*

## Deferred

| Item | Deferred to | Reason |
|---|---|---|
| Compaction procedure in Mode 3 | after a dry run on the largest retired register | Only one compaction has ever happened; write the procedure from that instance, not from theory |
| Offer bullet for Brief in the wiring block | the next block revision | Would make six freshly re-synced blocks stale (D-0009) |

## Next

1. Merge and tag `v0.3.0` after review.
2. Compaction dry run (separate long-running session; prompt handed over).
3. Run Doctor across the population again after the next round of installs and compare with the census.

## Open questions (owner)

*None open.*

*Bootstrap reminder: this is the first file to read each session. Close reminder: rewrite it AFTER the CHANGELOG entry — completed items out, new items in, past tense deleted.*
