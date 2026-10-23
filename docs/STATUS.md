# STATUS

*Last updated: 2026-10-23*

## Current phase

**v0.4.1 public (latest tag); Doctor 1.6.0 with `--json` on `main` (pull request #1, merged); LG-0044 reworked on draft pull request #2 and awaiting a new independent review.**

The 2026-10-23 review of #2 was PARTIAL: the binding rule holds, but the candidate could approve its own run. The rework moves the closing control outside the candidate. A trusted checkout's runner and validator judge a separate candidate tree, load their own code only from verified bytes under `python3 -I -B`, and refuse bytecode anywhere (D-0025, revised in place). Unreferenced old commits still open on GitHub by ID until GitHub Support purges them.

## In flight

`LEDGER.md` is authoritative: 4 live rows as of 2026-10-23, no P0/P1 (LG-0044 verifying; LG-0048, LG-0049 and LG-0050 open).

| Item | Owner | Target | Notes |
|---|---|---|---|
| New independent review of LG-0044 (`fix/lg-0044-acceptance-binding`, draft pull request #2) | owner's orchestrating session | next review | Must run the external check from a trusted checkout (`tests/README.md`); not to be merged before it passes |

## Blocked

*No items.*

## Found, not fixed

`tests.test_migrate_semantics` has 15 failures on recent CPython patch releases (3.10.21+, 3.11.16+, 3.12.14+, 3.13.15+, 3.14.7+). An `html.parser` change (gh-153030 / CVE-2026-15308) buffers the small `feed()` calls that `docs-migrate` makes when it scans HTML boundaries line by line. They are tracked as LG-0051 and fixed on a separate pull request; not this branch.

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
