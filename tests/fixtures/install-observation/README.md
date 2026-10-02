# Observed Install, then a fresh Bootstrap and Close

On 2026-09-11, two separate agent contexts (`fork_turns: none`) worked
sequentially on an invented Maple Check utility in an isolated system temporary
directory. This is an actual bounded agent-use observation, separate from the
template-derived automated installation fixture and authored lifecycle replays.

The first prompt supplied the project facts and installation request. The agent
read the complete skill and templates, installed four documentation files and
AGENTS, then ran Doctor and the utility. The second prompt requested only a
small authorized output change and verification. It supplied no expected
register edits or previous-agent transcript. That agent read the installed
AGENTS, STATUS, CHANGELOG, DECISIONS, README and skill, made the change and
performed Close. No adoption or wording decision was fabricated.

Retained artifacts:

- `install-prompt.txt` and `resume-prompt.txt`: dispatched prompts, with only
  scratch and skill paths normalized to labels.
- `before-install/`, `after-install/`, `after-close/`: complete project snapshots
  at those boundaries, including `check.py` and every installed document.
- `install-output.txt` and `resume-output.txt`: explicitly condensed agent
  reports of reads, commands, edits and limitations, not full tool transcripts.
- `observations.json`: artifact SHA-256 manifest, context count, limits and the
  primary session's independent checks.
- `primary-doctor-after-close.txt`: primary session's real Doctor output on
  the original temporary project after Close, exit 0 (16 PASS, 3 INFO, 3 SKIP).

Primary inspection verified the original CHANGELOG preamble and installation
entry remain byte-identical around the inserted new entry; DECISIONS is
unchanged and entry-free. The utility prints the exact authorized new sentence
and exits 0. Both snapshots contain exactly four docs, separate agent wiring,
no optional-file index entries for absent files, and no unused personal fields
or questions. The README was updated when its description became stale.

This is one small sequential exercise, not a compliance rate or a guarantee
about arbitrary agents. Snapshot bytes establish final state. The stated
CHANGELOG-before-STATUS write order is reported by the agent; there is no
independently captured filesystem timing trace. The exercise covers no Git,
ledger, owner-gated action or interruption. Running Doctor directly on the
retained copies adds an ancestor-register advisory because they now live inside
this repository; the recorded exit-0 observation used the system temporary
project. Recreate a snapshot in system temporary storage to repeat that check.
