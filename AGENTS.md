# project-docs-protocol · agent instructions

This directory is the skill itself. Editing it changes the protocol for every project that loads it (25 at the last census) and for Codex through the `~/.codex/skills/project-docs-protocol` symlink. Work on a branch; `main` stays at the last reviewed state.

## Project docs protocol

This project uses the project-docs-protocol (docs in `docs/`).

- **Session start:** before proposing or doing any work, read `docs/STATUS.md`
  (in full if it is under ~60 lines; otherwise its top line, its heading
  list, and the current-state sections only) and the last 3–5 entries of
  `docs/CHANGELOG.md`; skim `docs/DECISIONS.md` for entries touching the
  area you're about to work on.
- **After each meaningful unit of work** (spec drafted, decision made, blocker
  resolved, major refactor): append a CHANGELOG entry, then update STATUS.
  Do this as you go — do not wait for the session to end.
- **STATUS is rewritten, not appended.** Replace the current-state sections
  and bump the last-updated date. Never prepend a session record or leave a
  dated "done" section behind: that record belongs in CHANGELOG, and it must
  already be there before STATUS changes.
- CHANGELOG and DECISIONS are append-only: never edit past entries; append
  corrections or supersessions instead.
- **Precedence.** The three properties above — CHANGELOG before STATUS,
  STATUS rewritten, registers append-only — are the protocol's and are not
  overridden by project convention. Paths, id formats and entry shapes are
  this project's to set, here. If this file and the protocol disagree on one
  of those three properties, the disagreement is a CHANGELOG entry, not a
  habit.
