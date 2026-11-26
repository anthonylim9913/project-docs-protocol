# STATUS

*Last updated: 2026-11-26*

## Current phase

**v0.7.0 is the latest public tag: the delegation contract in the wiring
block, Doctor 1.9.1, and LG-0044 stage 1.**

An independent review of the candidate ran all three suites in a clean clone
and approved five ledger closures; two pre-publication checks then tightened
the delegation wording and bounded the unrecorded-commit check. Both
companions remain 0.2.2 with unchanged recorded `sha256v2:` identities.

After the tag, the tests workflow moved its Python 3.9 job to `ubuntu-24.04`
and one test stopped assuming an in-tree bytecode cache (CHANGELOG 2026-11-19).

Unreleased on `chore/release-tooling` (CHANGELOG 2026-11-26): a one-command
release gate (`scripts/release-check.py`), an optional privacy scan with a
sample pre-push hook (`scripts/leak-scan.py`), and CI on pinned Linux and
macOS images with a weekly run. Hosted CI has not run on these changes; the
macOS system interpreter on the hosted image is unverified.

Review limits: the non-UTF-8 filename case and three permission-mode subcases
skip on this filesystem and were not independently verified.

## In flight

`LEDGER.md` is authoritative: 5 OPEN and 0 VERIFYING live rows; no P0/P1.
LG-0052, LG-0056, LG-0057, LG-0058 and LG-0059 are CLOSED in the archive
with the independent reviewer's observations; 8 rows are archived.

| Work | Branch | End action |
|---|---|---|
| Delegated release tooling | `chore/release-tooling` | independent review, then owner decides on merge and hosted CI |

## Blocked

*No items.*

## Deferred

| Item | Deferred to | Reason |
|---|---|---|
| LG-0044 stage 2 | separate follow-up | Stage 1 is integrated; the self-approval gap remains OPEN under D-0029 |
| LG-0049 supplied-passage form and LG-0053 cache refusal | wave B | D-0030 and owner plan |
| LG-0048 registry pointer | wave C | D-0031; final-candidate registry gate still applies |
| LG-0060 temporary-directory isolation | separate test repair | Default-temp proofs only; fixtures inherit a parent register when TMPDIR is inside a checkout |
| Compaction procedure in Mode 3 | after a dry run | D-0005 remains current |
| Full CommonMark/GFM conformance | separate scope | Doctor and migration implement bounded, tested syntax |
| Re-syncing externally wired projects | their next Close | Missing current clauses WARN, never FAIL |

## Next

1. LG-0044 stage 2: the self-approval gap (D-0029).
2. LG-0060: make the test fixtures independent of where the temporary directory is.
3. Waves B and C: LG-0049, LG-0053, then LG-0048.
4. Decide whether the Doctor limits named in the v0.7.0 CHANGELOG entry become ledger rows.

## Open questions (owner)

*No open questions.*
