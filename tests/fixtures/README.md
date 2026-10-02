# Fixture notes

Fixtures contain invented, anonymised project text. `migration-20/STATUS.md`
models twenty live findings; an executable migration test reviews and writes
all twenty, checks the exact source-to-ID coverage and preserved STATUS bytes,
and applies a fresh plan to verify no additional rows or file changes.

`lifecycle/` contains authored before/after traces and an explicit explanation
of their executable oracles and limits. Scratch projects stay under
`tests/.tmp/`; no test reads a private project or requires a network service.
