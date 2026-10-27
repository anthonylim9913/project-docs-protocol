# STATUS

*Last updated: 2026-10-27*

## Current phase

**v0.4.1 public (latest tag); Doctor 1.6.0 with `--json` is on `main` (pull request #1 merged as `89ed3aa`), untagged.**

The local review branch is in progress and remains unpushed. Doctor, migration and Architect repairs have targeted regressions; checker documentation now matches measured behavior. The old/new Doctor comparison covers 5,789 qualifying registers with zero differing check lines. Research entry-point completion and final verification precede the final Close, which will reconcile the owner-verified merge and purge. No tag or remote write is authorized.

## In flight

`LEDGER.md` is authoritative: 5 live rows as of 2026-10-24, no P0/P1 (LG-0044, LG-0048, LG-0049 and LG-0050 open; LG-0051 verifying).

| Item | Owner | Target | Notes |
|---|---|---|---|
| Complete entry-point coverage, final verification and Close | reviewer, then owner | — | Both companion identities require independent review before owner recording |

## Blocked

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

1. **A usage error exits 2, the FAIL code (LG-0050): move it to 3, a change to the exit-code contract?** — proposed: exit 3, with a DECISIONS entry extending D-0013 — since 2026-10-23 — postponed by owner 2026-10-23, revisit when a consumer needs usage errors told apart by exit code
