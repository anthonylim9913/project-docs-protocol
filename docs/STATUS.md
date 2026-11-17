# STATUS

*Last updated: 2026-11-17*

## Current phase

**v0.6.0 is the latest public tag. This branch remains an unreleased
v0.7.0 candidate awaiting the owner's release gate.**

The independent reviewer approved five closures on `8059cdc` (2026-11-17);
the orchestrating session relayed that approval to this lane. Its clean-clone
proofs were 432 core / 123 research / 118 Architect OK, Doctor exit 0 and
registry PASS. No owner approval of those closures or release is claimed.
The pre-publication wording follow-up makes delegation duties explicit and
corrects approval provenance without changing Doctor behavior or version.
The lane's default-temp proofs pass: 432 core / 123 research / 118 Architect,
Doctor exit 0, registry PASS and git diff --check clean. This follow-up has
not received a new independent review.
Both companions remain 0.2.2 with unchanged recorded `sha256v2:` identities.
No tag, push or publication is authorized here.

Review limits: the non-UTF-8 filename case and three permission-mode subcases
skip on this filesystem and were not independently verified.

## In flight

`LEDGER.md` is authoritative: 5 OPEN and 0 VERIFYING live rows; no P0/P1.
LG-0052, LG-0056, LG-0057, LG-0058 and LG-0059 are CLOSED in the archive
with the independent observations and reviewer approval; 8 rows are archived.

| Item | Owner | Branch | End action |
|---|---|---|---|
| Release gate | owner | release/v0.7.0 | Approve release before publication or tags; no tag from this lane |

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

1. Obtain the owner's release gate for the unreleased v0.7.0 candidate.
2. Address LG-0044 stage 2, deferred waves and LG-0060 in separate scopes.

## Open questions (owner)

*No open questions.*
