# STATUS

*Last updated: 2026-10-29*

## Current phase

**v0.5.0 public; the open-items plan approved; wave A is next.**

The amended decisions D-0028–D-0032 govern implementation on this unreleased integration branch. Pull request #2 remains an open draft; LG-0044's unbound-input and self-judging gaps both remain OPEN until the staged repairs and independent review satisfy D-0029.

`.github/workflows/tests.yml` runs the suites, Doctor and the registry validator on pushes to `main` and on pull requests.

The unreleased integration branch includes Doctor 1.8.0 (D-0036): `wiring-path` compares a symlinked `docs/` by its selected label (LG-0056), and template residue is caught in STATUS and the docs README title (LG-0057, D-0037). Both rows are VERIFYING and await an independent review.

## In flight

`LEDGER.md` is authoritative: 4 OPEN and 3 VERIFYING live rows as of 2026-10-29, no P0/P1. LG-0044, LG-0052 and LG-0053 are P2; LG-0048, LG-0049, LG-0056 and LG-0057 are P3. LG-0050 is closed in the archive: usage errors keep exit 2 and the documentation now distinguishes them from reported FAILs (D-0032). LG-0052's v2 encoding is implemented and awaits its review and identity-recording gate; the registry's legacy identities are not release-ready.

| Item | Owner | Target | Notes |
|---|---|---|---|
| Prepare wave A implementation | implementation lanes | v0.6.0 | Follow D-0028, D-0029 and D-0032; preserve independent review and owner identity-recording gates |

## Blocked

*No items.*

## Deferred

| Item | Deferred to | Reason |
|---|---|---|
| Compaction procedure in Mode 3 | after a dry run | D-0005 remains current |
| Full CommonMark/GFM conformance | separate scope | Doctor and migration implement bounded, tested syntax |
| Re-syncing externally wired projects | their next Close | No check requires the change |

## Next

1. Wave A (v0.6.0): LG-0050 docs, LG-0052, LG-0044 stage 1. If stage 1 slips, ship without it and keep both LG-0044 gaps explicitly OPEN.
2. Wave B (v0.6.1): LG-0044 stage 2, LG-0049, LG-0053.
3. Wave C (v0.7.0): LG-0048.

## Open questions (owner)

*No items.*
