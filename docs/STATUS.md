# STATUS

*Last updated: 2026-11-17*

## Current phase

**v0.6.0 is the latest public tag: Doctor 1.8.0, `sha256v2:` registry
identities, a tests workflow, and `AGENTS.md` as the documented default.**

Both companions remain 0.2.2 with recorded `sha256v2:` identities. The next
candidate is being assembled from two local branches: LG-0044 stage 1 and the
delegation contract with Doctor 1.9.0.

## In flight

`LEDGER.md` is authoritative: 6 OPEN and 3 VERIFYING live rows; no P0/P1.
LG-0052, LG-0056 and LG-0057 remain VERIFYING for independent review.
LG-0050 is closed in the archive under D-0032.

| Item | Owner | Target | Notes |
|---|---|---|---|
| LG-0044 stage 1 | separate local branch | next candidate | Census work is separate; both acceptance gaps remain OPEN under D-0029 |
| LG-0058 delegation contract | separate local branch | next candidate | Built and judged once; the fix commit awaits re-review |
| LG-0059 uncovered commits advisory | separate local branch | next candidate | Built with the delegation branch; same review state |
| Closing review of LG-0052, LG-0056, LG-0057 | independent reviewer | next candidate | The v0.6.0 judge could not run on-disk tests in its sandbox |

## Blocked

*No items.*

## Deferred

| Item | Deferred to | Reason |
|---|---|---|
| LG-0049 supplied-passage form and LG-0053 cache refusal | wave B | D-0030 and owner plan |
| LG-0048 registry pointer | wave C | D-0031 |
| Compaction procedure in Mode 3 | after a dry run | D-0005 remains current |
| Full CommonMark/GFM conformance | separate scope | Doctor and migration implement bounded, tested syntax |
| Re-syncing externally wired projects | their next Close | No check requires the change |

## Next

1. Merge LG-0044 stage 1 and the delegation branch onto v0.6.0, and re-review the delegation fix commit.
2. Close LG-0052, LG-0056 and LG-0057 with a reviewer that can run the on-disk tests.
3. LG-0044 stage 2 (the self-approval gap), then waves B and C.

## Open questions (owner)

*No open questions.*
