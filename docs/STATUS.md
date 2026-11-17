# STATUS

*Last updated: 2026-11-17*

## Current phase

**v0.6.0 is the latest public tag. This branch is an unreleased v0.7.0
candidate awaiting independent review and the owner's release gate.**

`release/v0.7.0` integrates LG-0044 stage 1 and the delegation contract with
Doctor 1.9.0, in that order. The merged core suite passes 432 tests (one skip).
Both companions remain 0.2.2 with unchanged recorded `sha256v2:` identities.
No tag, push or publication is authorized here.

## In flight

`LEDGER.md` is authoritative: 5 OPEN and 5 VERIFYING live rows; no P0/P1.
LG-0052, LG-0056, LG-0057, LG-0058 and LG-0059 remain VERIFYING.
LG-0050 is closed in the archive under D-0032.

| Item | Owner | Branch | End action |
|---|---|---|---|
| Candidate and five VERIFYING rows | independent reviewer | release/v0.7.0 | Review the exact candidate and run on-disk proofs; close rows only on acceptance |
| Release gate | owner | release/v0.7.0 | Approve release only after independent review; no tag from this lane |

## Blocked

*No items.*

## Deferred

| Item | Deferred to | Reason |
|---|---|---|
| LG-0044 stage 2 | after candidate review | Stage 1 is integrated; the self-approval gap remains OPEN under D-0029 |
| LG-0049 supplied-passage form and LG-0053 cache refusal | wave B | D-0030 and owner plan |
| LG-0048 registry pointer | wave C | D-0031; final-candidate registry gate still applies |
| LG-0060 temporary-directory isolation | separate test repair | Default-temp proofs only; fixtures inherit a parent register when TMPDIR is inside a checkout |
| Compaction procedure in Mode 3 | after a dry run | D-0005 remains current |
| Full CommonMark/GFM conformance | separate scope | Doctor and migration implement bounded, tested syntax |
| Re-syncing externally wired projects | their next Close | Missing current clauses WARN, never FAIL |

## Next

1. Independently review the v0.7.0 candidate and all five VERIFYING rows.
2. Obtain the owner's release gate before any publication or tag.
3. Address LG-0044 stage 2, deferred waves and LG-0060 in separate scopes.

## Open questions (owner)

*No open questions.*
