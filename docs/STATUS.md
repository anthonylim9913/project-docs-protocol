# STATUS

*Last updated: 2026-10-02*

## Current phase

**v0.4.0 public with cleaned history; independent review and the LG-0046 fresh-session test queued.**

The research and Architect companions, the skill registry and Doctor 1.5.0 are released. Unreferenced old commits still open on GitHub by ID until GitHub Support purges them (request sent 2026-10-02).

## In flight

`LEDGER.md` is authoritative: 4 live rows as of 2026-10-02, no P0/P1.

| Item | Owner | Target | Notes |
|---|---|---|---|
| Independent review of v0.4.0 and branch fix/research-index-scope | review session | next | Settles LG-0044, LG-0045 and LG-0047 |
| LG-0046 fresh-session scenarios S1–S3 | owner starts, agent scores | next | Throwaway fixture outside this repository |

## Blocked

*No items.*

## Deferred

| Item | Deferred to | Reason |
|---|---|---|
| Compaction procedure in Mode 3 | after a dry run | D-0005 remains current |
| Full CommonMark/GFM conformance | separate scope | Doctor and migration implement bounded, tested syntax |
| Re-syncing externally wired projects | their next Close | No check requires the change |

## Next

1. Score the three LG-0046 sessions; fix the protocol text where a scenario fails for the text's sake.
2. Act on the review: merge fix/research-index-scope and record its reviewed digest if it passes.
3. GitHub Support confirms the purge.

## Open questions (owner)

1. **Copyright line: keep the full name, or use the GitHub handle?** — proposed: the handle, applied to every release with one more history rewrite — since 2026-10-02
