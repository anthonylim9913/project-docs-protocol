# STATUS

*Last updated: 2026-11-16*

## Current phase

**v0.5.0 is still the latest public tag. `release/v0.6.0` is an unreleased
v0.6.0 candidate awaiting independent review and the owner's release gate.**

The candidate integrates CI/README accuracy, Doctor 1.8.0, D-0028–D-0032,
LG-0050 documentation and LG-0052's sha256v2 encoding. Both companions remain
0.2.2 with owner-approved transferred identities. No tag or push is made.

The prior candidate's independent review found stale identity descriptions
and an ineffective CI whitespace range. This revision corrects both; the
candidate still awaits independent re-review and owner release approval.

## In flight

`LEDGER.md` is authoritative: 6 OPEN and 3 VERIFYING live rows; no P0/P1.
LG-0052, LG-0056 and LG-0057 remain VERIFYING for independent review.
LG-0050 is closed in the archive under D-0032.

| Item | Owner | Target | Notes |
|---|---|---|---|
| LG-0044 stage 1 | separate local branch | next candidate | Census work is separate; both acceptance gaps remain OPEN under D-0029 |
| LG-0058 delegation contract | separate local branch | independent review | Only the finding is recorded here; no delegation text changed |
| LG-0059 uncovered commits advisory | separate local branch | independent review | Only the finding is recorded here; threshold and implementation remain separate |
| Review this candidate | independent reviewer, then owner | v0.6.0 | Review LG-0052 and Doctor fixes; owner controls release |

## Blocked

*No items.*

## Deferred

| Item | Deferred to | Reason |
|---|---|---|
| LG-0049 supplied-passage form and LG-0053 cache refusal | wave B | D-0030 and owner plan; not part of this candidate |
| LG-0048 registry pointer | wave C | D-0031; the final-candidate registry gate still applies |
| Compaction procedure in Mode 3 | after a dry run | D-0005 remains current |
| Full CommonMark/GFM conformance | separate scope | Doctor and migration implement bounded, tested syntax |
| Re-syncing externally wired projects | their next Close | No check requires the change |

## Next

1. Keep all final proof commands green on the candidate sent for re-review.
2. Independently review this branch; retain the VERIFYING rows until review.
3. Obtain the owner's release gate before any publication or tag.

## Open questions (owner)

*No new questions; publication remains gated on review and owner approval.*
