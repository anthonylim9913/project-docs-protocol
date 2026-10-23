# Doctor JSON-mode fixtures

Three invented projects for `test_doctor_json.py`, each a complete four-file
register with a ledger and the authentic Install step 2 wiring block in
`AGENTS.md`:

- `pass/` — every check passes; exit 0.
- `warn/` — the same project with no install footer in `docs/README.md`; one
  `readme-footer` WARN, exit 1.
- `fail/` — the same project with `D-0001` used twice in `DECISIONS.md`; one
  `decisions-ids` FAIL, exit 2.

The test copies each into a system temporary directory, outside this
repository's own register, so no `nested-register` advisory changes the exit
code. Two exit-3 cases, `no-register` and `bad-today`, use an empty directory
the test creates.

`baseline.json` and `baseline/*.stdout` are the text-mode output of
`scripts/docs-doctor.py` at `6c96571` (v0.4.1, Doctor 1.5.0), before `--json`
existed, on Python 3.14.4, with the arguments recorded per case. The manifest
records that script's SHA-256, each case's exit code, stdout digest and exact
stderr. The text-mode test compares stdout byte for byte; the only allowed
difference is the version number on the header line, so a version bump does
not force a recapture. Recapture only when a change is meant to alter text
output, say so in that change's CHANGELOG entry, and record the commit the new
baseline came from.
