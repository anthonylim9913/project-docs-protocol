# LEDGER

*The single live tracker of findings, checks and open problems — one row per item, updated
in place; anything with a closing condition or an evidence cell lives here and nowhere
else, but only while its state can still change: a finding that is terminal at birth (a
confirmation, a lesson, praise, a wave narrative) is CHANGELOG material, never a ledger
row. Live rows only: a row entering CLOSED, NOT-AN-ISSUE or SUPERSEDED moves verbatim to
`LEDGER-ARCHIVE.md` — this file's header and separator rows, no banner; append-only, never
read at bootstrap — in the same edit that changes its state. A state change is an edit to
the row, not a new row; it goes to CHANGELOG when CHANGELOG-worthy — batch a triage pass
as one entry.*

## Rules — this banner is the schema; the doctor checks rows against it

- **Ids** are minted once, monotonic, never reused or renumbered: `LG-0001`, `LG-0002`, …
  (a family prefix like `UI-LG-0001` is allowed if declared here). Other registers cite ids.
  Allocate above the highest number in that series across live rows, archive rows,
  and reservations in CHANGELOG, LEDGER-RESERVATIONS.md and LEDGER-ENTRIES-OWED.md.
  Compare numeric identity: LG-1 and LG-0001 reserve the same address. Never
  convert more than twelve decimal digits; stop allocation on malformed IDs.
- **P** is one token: `P0` (drop everything) · `P1` · `P2` · `P3` (someday).
- **Status is one token** from exactly: `OPEN` · `BLOCKED` · `VERIFYING` · `CLOSED` ·
  `NOT-AN-ISSUE` · `SUPERSEDED`. Actions, commands, verdicts and sequencing notes are not
  statuses — they belong in Evidence, STATUS.md, or a plan.
- **Transitions:** OPEN ↔ BLOCKED. OPEN → VERIFYING (fix applied, confirming stability) →
  CLOSED, or back to OPEN. Any state → SUPERSEDED — Evidence MUST name the successor row id.
  Any state → NOT-AN-ISSUE (won't-fix, disproven, withdrawn) — Evidence quotes the ruling or
  the disproving reading or command; a bare verdict ("REFUTED") is not a disproof. Where
  re-minting is a real risk the row may stay live as a tombstone: Status stays NOT-AN-ISSUE
  and the Title is prefixed `DO-NOT-RESURRECT` — the token the doctor's terminal-leak check excepts.
- **CLOSED requires, in Evidence at close time:** (a) a repo-resolving pointer — commit
  sha, check file, or path; (b) the command or check name plus its current reading; (c)
  committed work in a git project, or the durable artifact/hash contract below
  for a non-git project. "By me", bare "done", a decision id, or a future-work note close nothing.
- **Reopen** mints nothing: log the reason in CHANGELOG first, then append
  `REOPENED YYYY-MM-DD LG-NNNN archive-sha256:<hash> → live` to the archive.
  The hash is SHA-256 of the exact most recent terminal row text in UTF-8,
  excluding its newline. Verify the marker, then restore that item to the live
  file under its original id, with a live status and updated date/evidence.
  A retry verifies the same marker and restores only a missing live row; a
  conflicting live row stops the repair. A later close appends a new terminal
  row; old rows and markers are never rewritten. Doctor conservatively flags
  the live/archive collision during reopen; manually verify this event and
  identity before treating it as a deliberate reopen rather than ID reuse.
- **Closes-when is written when the row is opened**, as a yes/no condition — a one-line
  command or observation that either holds or doesn't. Never a status word, never a plan.
- **Tags** are one axis (area or theme): a closed set declared on the one line below whose
  first non-blank characters are `Tags:`, and nowhere else — at most twelve `+tokens` — a token is `+`, a lowercase letter, then lowercase letters, digits or hyphens (`+auth`, `+phone-v4`); anything else is text, not a tag; a
  Tags cell is blank or holds declared tokens only. Grouping is a derived view — `grep
  '+auth' LEDGER.md` — never a sort: file order is mint order and is never regrouped.
  Tags:
- **Blocked-on has one job:** a BLOCKED row names at least one gate — a live row id,
  the word `owner`, or a named external gate; every other state leaves it blank.
- **Archive lifecycle:** CHANGELOG first, naming the ID and terminal outcome;
  then write the terminal row to `LEDGER-ARCHIVE.md`, read it back and verify
  the ID and every cell, remove the live row, then rewrite STATUS. Replay uses
  the logged event: verify an identical archive copy instead of appending it
  again. Only the live predecessor or identical terminal row may be removed;
  conflicting content stops the repair without overwriting data. After a
  verified reopen, a subsequent close appends its own terminal row/event.
- **Non-git closure:** git is recommended but not required. In a non-git project,
  CLOSED Evidence must name a durable artifact path, content hash, and a
  reproducible command and reading; in a git project it may use a commit SHA.
- **Lineage:** a clarification is an edit to the row; a sub-item is a new id whose Evidence
  opens `from LG-NNNN`; children are found by grep on the id. No links column, no "see".
- **Update rows in place; append only genuinely new items** — search by id, Tags, Touches
  or title first; new ids at the bottom, never a new table, section, or sibling file. Prior
  readings live in git history; Evidence keeps only the current one.
- **Date** is the row's last touch — any edit bumps it (YYYY-MM-DD). A long-untouched
  OPEN or VERIFYING row is a triage prompt: the doctor flags it, a dated triage note in
  Evidence uses `TRIAGE YYYY-MM-DD: <observation>` to reset the clock; an
  arbitrary deadline does not. Nothing is ever auto-closed for staleness.
- **Executable checks live in the project's gate or test runner**, not here; a row cites
  its gate by filename. Open-item counts are derived by reading this table, never authored.
- **Parser rules:** one row = one physical line, never wrapped (this banner wraps; rows do
  not); the header row matches the template's with cells trimmed and case exact, the
  separator row is free; more than one table in this file is a FAIL; a pipe inside a cell
  is written `\|`, as the example row's Evidence shows.

## Items

| ID | P | Status | Date | Title | Tags | Closes-when | Blocked-on | Touches | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| LG-0001 | P1 | OPEN | YYYY-MM-DD | one-line finding or check | | `command → expected reading` | | path or area | origin pointer; a pipe in a cell is written \| |
