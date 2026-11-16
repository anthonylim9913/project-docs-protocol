# STATUS

*Last updated: 2026-11-16*

## Current phase

**v0.5.0 is still the latest public tag. The unreleased v0.6.0 candidate and
Doctor 1.9.0 delegation lane await independent review and the owner's release gate.**

The delegation contract and uncovered-commits advisory are local candidates,
not releases. Both companions remain at their owner-approved 0.2.2 identities.

## In flight

`LEDGER.md` is authoritative: 4 OPEN and 5 VERIFYING live rows; no P0/P1.
LG-0052, LG-0056, LG-0057, LG-0058 and LG-0059 need independent review.

| Item | Owner | Branch | End action |
|---|---|---|---|
| LG-0058/LG-0059 review | independent reviewer | feat/delegation-recording | Review developer evidence, then close or return findings |
| Candidate release review | reviewer, then owner | release/v0.6.0 | Review VERIFYING rows and obtain publication approval |

## Blocked

*No items.*

## Deferred

| Item | Deferred to | Reason |
|---|---|---|
| LG-0044 acceptance census | separate candidate | D-0029; both acceptance gaps remain OPEN |
| LG-0049 supplied-passage form and LG-0053 cache refusal | wave B | D-0030 and owner plan |
| LG-0048 registry pointer | wave C | D-0031; final-candidate registry gate still applies |
| Compaction procedure | after a dry run | D-0005 remains current |
| Full CommonMark/GFM conformance | separate scope | Doctor and migration implement bounded syntax |
| External wiring re-sync | each project's next Close | Missing clauses WARN, not FAIL |

## Next

1. Independently review LG-0058/LG-0059 on the delegation branch.
2. Assemble and review the candidate; retain VERIFYING rows until that review.
3. Obtain the owner's release gate before publication or tags.

## Open questions (owner)

*No new questions; publication remains gated on review and owner approval.*
