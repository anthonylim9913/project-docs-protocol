# architect-protocol candidate

This optional skill gives a project a small, reviewable packet for staged
architecture work. It preserves the project's existing `docs/STATUS.md`,
`CHANGELOG.md`, `DECISIONS.md`, and optional `LEDGER.md`; the Architect packet
does not create competing registers.

Copy or adapt the four files under `docs/architect/` only when the project has
an Architect/Developer/Reviewer split. Start with `PLAN.md` and `STAGES.md`,
record acceptance controls in `ACCEPTANCE-MATRIX.md`, and keep current stage
and subject identity in `STATE.json`. The lifecycle is:

`scope → baseline → implement → review → repair → handoff`

Each stage is reviewed from a clean, exact subject in a separate read-only
checkout. Reviewers independently hash all declared inputs and exercise both
success and failure controls. A missing artifact, dirty subject, stale hash,
unverified identity, or incomplete diagnostic is a failed or incomplete
review, not a pass.

Read [SCHEMA.md](SCHEMA.md) for schema 2, historical receipt compatibility and
acyclic B/F/J handoff binding. Run production packet validation from a clean
project checkout (Python 3.9+, Git and safe POSIX descriptors):

```bash
python3 -B /path/to/architect-protocol/scripts/architect-doctor.py .
```

An absent `docs/architect/` directory is valid and produces `SKIP`; a partial
or malformed packet fails. This candidate is not globally activated.

The minimal example is intentionally unfrozen. Run it with
`python3 -B scripts/architect-doctor.py examples/minimal --structural-example`.
It returns STRUCTURAL, not production acceptance. Ordinary invocation refuses
example mode. Optional absence still returns SKIP, while malformed present
packets fail. Keep one writer for the project registers and preserve failed
review attempts. A structural check cannot replace independent stage review or
the actual Architect's response.
