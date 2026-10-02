- Parent
2. - ```markdown
     ## Project docs protocol

     This project uses the project-docs-protocol (docs in `docs/`).

     - **Session start:** before proposing or doing any work, read `STATUS.md`
       (in full if it is under ~60 lines; otherwise its top line, its heading
       list, and the current-state sections only) and the last 3–5 entries of
       `CHANGELOG.md`; skim `DECISIONS.md` for entries touching the area you're
       about to work on; then read live `LEDGER.md` rows if installed.
     - **After each meaningful unit of work** (spec drafted, decision made, blocker
       resolved, major refactor): write CHANGELOG first, edit LEDGER if installed,
       then rewrite STATUS. Brief records reserved DECISIONS entries between
       CHANGELOG and LEDGER; ordinary Close adds optional DECISIONS after STATUS.
       Do this as you go — do not wait for the session to end.
     - **STATUS is rewritten, not appended.** Replace the current-state sections
       and bump the last-updated date. Never prepend a session record or leave a
       dated "done" section behind: that record belongs in CHANGELOG, and it must
       already be there before STATUS changes.
     - CHANGELOG and DECISIONS are append-only: never edit past entries; append
       corrections or supersessions instead.
     - **Precedence.** The three properties above — CHANGELOG before LEDGER before STATUS
       (skip LEDGER when absent),
       STATUS rewritten, registers append-only — are the protocol's and are not
       overridden by project convention. Paths, id formats and entry shapes are
       this project's to set, here. If this file and the protocol disagree on one
       of those three properties, the disagreement is a CHANGELOG entry, not a
       habit.
     ```
