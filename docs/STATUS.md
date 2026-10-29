# STATUS

*Last updated: 2026-10-29*

## Current phase

**v0.5.0 is the latest public tag: the independently reviewed fail-closed repairs, Doctor 1.7.0, and both companion identities recorded at 0.2.2.**

Pull request #2 (LG-0044) is still an open draft; neither candidate branch closes its gate unchanged. The owner has a plan for the five open ledger rows.

A draft branch, `fix/doctor-symlink-and-residue`, moves Doctor to 1.8.0 (D-0036): `wiring-path` compares a symlinked `docs/` by its selected label (LG-0056), and template residue is caught in STATUS and the docs README title (LG-0057, D-0037). Both rows are VERIFYING and await an independent review.

## In flight

`LEDGER.md` is authoritative: 5 OPEN and 2 VERIFYING live rows as of 2026-10-29, no P0/P1. LG-0044 and LG-0052 are P2; LG-0048, LG-0049, LG-0050, LG-0056 and LG-0057 are P3.

| Item | Owner | Target | Notes |
|---|---|---|---|
| Choose a versioned, unambiguous Content-ID transition (LG-0052) | owner | — | Different trees can share the current framed digest; refreshing identities does not fix this |

## Blocked

*No items.*

## Deferred

| Item | Deferred to | Reason |
|---|---|---|
| Compaction procedure in Mode 3 | after a dry run | D-0005 remains current |
| Full CommonMark/GFM conformance | separate scope | Doctor and migration implement bounded, tested syntax |
| Re-syncing externally wired projects | their next Close | No check requires the change |

## Next

1. Repair LG-0044 on a candidate whose inventory fails closed, rebased onto v0.5.0, and independently re-review it.
2. Settle LG-0052's identity format before LG-0048 adds a registry pointer to Doctor.
3. Settle LG-0049's supplied-passage record form, with a research companion re-review.

## Open questions (owner)

1. **A usage error exits 2, the FAIL code (LG-0050): move it to 3, a change to the exit-code contract?** — proposed: exit 3, with a DECISIONS entry extending D-0013 — since 2026-10-23 — postponed by owner 2026-10-23, revisit when a consumer needs usage errors told apart by exit code
2. **Which versioned Content-ID encoding and legacy transition should replace ambiguous framing (LG-0052)?** — proposed: review an injective versioned format with explicit legacy handling before adoption — since 2026-10-27
