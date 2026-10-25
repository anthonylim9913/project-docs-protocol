# STATUS

*Last updated: 2026-10-25*

## Current phase

**v0.4.1 public (latest tag); Doctor 1.6.0 with `--json` and the LG-0051 migration fix are on `main` (pull requests #1 and #3, merged), untagged; LG-0044 is reworked on `fix/lg-0044-acceptance-binding-alt` and awaits a new independent review.**

The 2026-10-23 review of the LG-0044 fix was PARTIAL: the binding rule holds, but the candidate could approve its own run. The rework moves the closing control outside the candidate: a trusted checkout's runner and validator judge a separate candidate tree, load their own code only from verified bytes under `python3 -I -B`, and refuse bytecode anywhere (D-0025). `main` (`66c11c3`) is merged into the branch. Unreferenced old commits still open on GitHub by ID until GitHub Support purges them.

## In flight

`LEDGER.md` is authoritative: 5 live rows as of 2026-10-25, no P0/P1 (LG-0044 and LG-0051 verifying; LG-0048, LG-0049 and LG-0050 open).

| Item | Owner | Target | Notes |
|---|---|---|---|
| New independent review of LG-0044 (`fix/lg-0044-acceptance-binding-alt`) | owner's orchestrating session | next review | Must run the external check from a trusted checkout (`tests/README.md`); not to be merged before it passes |
| Close LG-0051 | owner | — | Pull request #3 merged as `66c11c3` on 2026-10-25 |

## Blocked

*No items.*

## Deferred

| Item | Deferred to | Reason |
|---|---|---|
| Compaction procedure in Mode 3 | after a dry run | D-0005 remains current |
| Full CommonMark/GFM conformance | separate scope | Doctor and migration implement bounded, tested syntax |
| Re-syncing externally wired projects | their next Close | No check requires the change |

## Next

1. Review LG-0044 independently, running the external check from a trusted checkout of the reviewed commit and pinning its `tests/harness.sha256`; then give Doctor a pointer to the registry validator (LG-0048).
2. Fix the re-review's deferred notes (LG-0049), with a re-review of any companion touched.
3. GitHub Support confirms the purge, including the follow-up commit.

## Open questions (owner)

1. **A usage error exits 2, the FAIL code (LG-0050): move it to 3, a change to the exit-code contract?** — proposed: exit 3, with a DECISIONS entry extending D-0013 — since 2026-10-23 — postponed by owner 2026-10-23, revisit when a consumer needs usage errors told apart by exit code
2. **Which checkout is "trusted" for a harness change?** — proposed: the reviewed commit, checked out again in a separate directory, with the pin from `sha256sum tests/harness.sha256` published in the review — since 2026-10-23
