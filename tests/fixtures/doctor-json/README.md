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
stderr. The text-mode test verifies each captured stdout digest before comparing
stdout byte for byte, with exactly these expected-output transformations:

- Replace only the header's Doctor version with the current version.
- Replace the exact three-clause `wiring-clauses` PASS text with the four-clause
  text adding `delegation`, because the project fixtures carry the current block.
- After `git-status-churn`, insert the `git-unrecorded-commits` SKIP line with
  `git checks disabled (--no-git)`, matching the recorded arguments.
- For register cases only, increase total checks and skipped checks by one;
  leave every other summary count, diagnostic, exit code and stderr unchanged.

These are explicit expected deltas from the immutable Doctor 1.5.0 capture,
not output copied from the running Doctor. Exact comparison still detects any
other change; independent delegation and temporary-Git-repository regressions
exercise the new behavior. No recapture is needed for these approved deltas.
For any other intentional text-output change, recapture, say so in that change's
CHANGELOG entry, and record the commit the new baseline came from.
