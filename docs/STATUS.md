# STATUS

*Last updated: 2026-10-05*

## Current phase

**v0.4.1 public: the reviewed fixes, recorded companion digests, and the README rewritten as a continuity system.**

Both companions validate against digests recorded after an independent re-review. Unreferenced old commits still open on GitHub by ID until GitHub Support purges them.

## In flight

`LEDGER.md` is authoritative: 3 live rows as of 2026-10-05, no P0/P1 (LG-0044 open, LG-0047 verifying, LG-0048 open).

| Item | Owner | Target | Notes |
|---|---|---|---|
| Narrow re-review of release/v0.4.1 (both companions and the registry digest change) | review session | next | One session, no agents; PASS/FAIL per companion and the digests to record |
| Record the reviewed digests, merge, tag v0.4.1, push | owner, then agent | after the re-review | |

*No items.*

## Deferred

| Item | Deferred to | Reason |
|---|---|---|
| Compaction procedure in Mode 3 | after a dry run | D-0005 remains current |
| Full CommonMark/GFM conformance | separate scope | Doctor and migration implement bounded, tested syntax |
| Re-syncing externally wired projects | their next Close | No check requires the change |

## Next

1. Close the acceptance-harness gaps (LG-0044) and give Doctor a pointer to the registry validator (LG-0048).
2. Fix the re-review's deferred notes (LG-0049), with a re-review of any companion touched.
3. GitHub Support confirms the purge, including the follow-up commit.

## Open questions (owner)

*None open.*
