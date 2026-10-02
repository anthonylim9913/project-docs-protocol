# Lifecycle replay evidence

Run `python3 -B -m unittest tests.test_lifecycle -v` at the repository root.
These are authored protocol examples with executable invariants, not traces
captured from an autonomous Brief/Close implementation. The skill ships no
automatic writer for those modes. Independent agent-consumption exercises must
be assessed separately; this suite does not claim an agent compliance rate.

Each JSON file contains an owner exchange, starting file contents, and named
edits. The test writes those recorded bytes into an isolated project under
`tests/.tmp/`, runs the actual `scripts/docs-doctor.py`, checks its exit and
diagnostics, and verifies that Doctor leaves every file byte unchanged.
`base.json` supplies the small installed register shared by the examples.
The repository's active AGENTS wiring is copied into each scratch project.
All retained examples use invented project content and the fixed test date
2026-09-10.

| Trace | Executable evidence |
|---|---|
| `brief-authorized.json` | Delegated single-option action has a local artifact and CHANGELOG record without a fabricated decision. |
| `brief-gated.json` | Silence leaves the exact owner question and ledger gate intact. |
| `brief-method-only.json` | Method selection leaves the separate execution gate intact. |
| `brief-mixed.json` | Two of five answers; one actual decision, one default with no D-ID; three questions and rows unchanged; external and row blockers survive; a terminal ruling cites its owner provenance. Doctor warns between CHANGELOG reservation and decision append and fails during temporary live/archive overlap. |
| `interrupted-brief.json` | Missing reserved IDs remain visible after an intervening Close uses the next ID. Each partial repair resolves only its missing citation; all prior decision bytes survive. Repeated Doctor runs preserve the recovered state. An alternate conflicting-content branch demonstrates that resolving an ID does not verify its meaning. |
| `archive-reopen.json` | Archive copy matches every cell before live removal. Repeated checks preserve the row; an alternate conflicting live copy is flagged. Reopen retains the original ID and hashes the exact archived row. A real local check and independent SHA-256 comparison verify non-git evidence and fail when the artifact is changed. |

The test methods choose the named edit sequence. `conflicting-decisions` and
`conflicting-live-copy` are alternate branches, not steps following successful
recovery. A full-file recorded edit is not a production recovery algorithm;
rewriting a snapshot is not counted as proof of writer idempotence.

Known diagnostics are asserted, not suppressed. Every scratch project is
inside this repository, so Doctor reports `WARN nested-register` and the
otherwise-clean fixture exit is 1. Correct append-only reservation recovery
after an intervening Close can leave IDs physically out of numeric order;
the example currently expects `WARN decisions-order`. Doctor deliberately
reports `FAIL ledger-archive-ids` for a reopened row as well as an accidental
collision. The reopen event uses
`REOPENED YYYY-MM-DD LG-NNNN archive-sha256:<digest> → live`, where the digest
is SHA-256 of the exact archived row's UTF-8 bytes, excluding the newline.
The oracle verifies that linkage; Doctor does not interpret the event.

Doctor checks the shape of CLOSED evidence, not its truth. The durable-artifact
test makes that boundary observable: after artifact corruption the command
and hash fail, while Doctor still passes `ledger-evidence`. Authorization,
owner reasoning, semantic conflicts, and the choice of edits remain agent or
human responsibilities.
