# STATUS

*Last updated: 2026-10-27*

## Current phase

**v0.4.1 remains the latest public tag. Doctor 1.6.0 and the PR #3 migration repair are on main, untagged.**

PR #3 merged on 2026-10-25 (b9ac127, 66c11c3); LG-0051 is CLOSED in the archive after independent native Python 3.14.7 verification. The owner confirms the completed purge of all 30 old GitHub commit IDs. The local review branch is unpushed and awaiting the owner; pull request #2 (LG-0044) is still an open draft. Round-three repairs narrow migration's over-refusal without pruning reservations, remove Doctor's duplicate failure, and clarify checker documentation and Architect errors. No release or remote write is authorized.

## In flight

`LEDGER.md` is authoritative: 5 OPEN live rows as of 2026-10-27, no P0/P1. LG-0044 and LG-0052 are P2; LG-0048, LG-0049 and LG-0050 are P3.

| Item | Owner | Target | Notes |
|---|---|---|---|
| Review the local repairs and changed companions | owner and independent reviewer | — | Both companion identities are intentionally stale; retain their core fallbacks until review and owner recording |
| Choose a versioned, unambiguous Content-ID transition (LG-0052) | owner | — | Different trees can share the current framed digest; refreshing identities does not fix this |

## Blocked

0 BLOCKED ledger rows as of 2026-10-27 — `LEDGER.md`.

| Item | Blocked by | Unblocks when |
|---|---|---|
| Use the changed companions | Independent reviewer gates and owner recording | Both gates pass and the owner records the reviewed identities |

## Deferred

| Item | Deferred to | Reason |
|---|---|---|
| Compaction procedure in Mode 3 | after a dry run | D-0005 remains current |
| Full CommonMark/GFM conformance | separate scope | Doctor and migration implement bounded, tested syntax |
| Re-syncing externally wired projects | their next Close | No check requires the change |

## Next

1. Owner reviews the local, unpushed branch and arranges independent companion re-review.
2. Plan the LG-0052 identity-format transition and independent verification.
3. Repair and independently re-review LG-0044; neither candidate closes its gate unchanged.
4. Add the registry-validator pointer (LG-0048) with compatibility checks, and settle LG-0049's supplied-passage record form.

## Open questions (owner)

1. **A usage error exits 2, the FAIL code (LG-0050): move it to 3, a change to the exit-code contract?** — proposed: exit 3, with a DECISIONS entry extending D-0013 — since 2026-10-23 — postponed by owner 2026-10-23, revisit when a consumer needs usage errors told apart by exit code
2. **Which versioned Content-ID encoding and legacy transition should replace ambiguous framing (LG-0052)?** — proposed: review an injective versioned format with explicit legacy handling before adoption — since 2026-10-27
3. **Refresh the changed companion identities after review?** — proposed: independently re-review both companions before the owner records either identity — since 2026-10-27
