# Independent reviewer probes

A read-only reviewer created a separate 1,098-case sweep around the authentic
Install Step 2 block, without importing the authored test case list.
`run_sweep.py` is the exact generator, relocated to find the repository from
this directory. It needs the ignored development parser environment and writes
its observations to system temporary storage. It never changes a project.

```sh
tests/.tmp/markdown-oracle-venv/bin/python -B tests/fixtures/markdown-oracle/reviewer-probes/run_sweep.py
```

`red-mismatches.json` retains every mismatch's full source, parser block tokens
and Doctor-visible lines. `red-cli.json` retains the two independently seeded
full CLI confirmations, with generated temporary paths omitted. The sweep
found 16 disagreements among 1,098 complete Install wrappers. Both CLI cases
left their scratch project bytes unchanged. The four-space continuation
wrongly passed all wiring checks (exit 0); the seven-space continuation was
wrongly rejected (exit 2). Both begin with the ordered siblings `1. Outer` and
`  2. Inner` followed by one blank line.

The source hash in the JSON files identifies the reviewed Doctor revision.
`red-visibility-helper.txt` retains its relevant implementation before repair.
The initial sweep establishes only the installation sentence's visibility in
these generated wrappers; the two CLI confirmations also check all three
wiring outcomes. It does not establish general CommonMark or GFM conformance,
semantic correctness, or agent behavior.

After the sibling repair, `green-sweep.json` records all 1,098 independent
sentence-visibility observations with zero disagreements. Each regenerated
input is identified by its case name and source SHA-256; the exact Install
block is retained once. `green-cli.json` records 15 separately seeded full CLI
runs, including the required authentic six-space nested block, all three
bullet kinds, numbered containers, tab stops, blank/tight layouts, lazy
paragraph continuation, original top-level code and both ordered-sibling
counterexamples. Each run reached later checks, had the expected exit and
three wiring outcomes, and preserved every project byte.

```sh
tests/.tmp/markdown-oracle-venv/bin/python -B tests/fixtures/markdown-oracle/reviewer-probes/run_cli.py
python3 -B tests/fixtures/markdown-oracle/reviewer-probes/run_discovery.py
```

`run_discovery.py` uses independent temporary projects and actual Doctor and
migration CLIs. `discovery-observations.json` retains the complete outcome
matrix: root-only, docs-only, empty docs, complete root beside two-file docs,
partial root beside complete docs, both directions of explicit selection
between two complete registers, a custom explicit directory, ambiguous
ownership refusal, explicit pre-install requirements, and target binding
before prepared-journal replay. Successful migrations changed only selected
outputs. A copied matching prepared journal did not allow the plan to write
to a different identical register; the intended target resumed and the same
plan repeated without mutation. One initial reviewer harness run stopped
because macOS's `/var` and `/private/var` aliases differed during a path
comparison; canonicalizing the scratch root fixed that harness issue before
the retained successful run. This was not a product finding.

The initial ordered-sibling failure was a confirmed product defect, not a
retained acceptance exception. Its repair was independently reread and the
same probes passed afterward. The retained source hashes establish the exact
reviewed runtime revisions. No repository registers or unrelated projects
were edited by the reviewer.

A bounded final follow-up reran the same discovery matrix after the separate
migration semantic repairs. `discovery-observations-final.json` records that
successful rerun at migration SHA-256
`dff2647f5e4594abaaff8d38f21791d421add7e1fb64d2247f73bc3e43c92d88`;
Doctor and the shared selector retain the hashes from the first green run.
All eleven discovery/replay outcomes are identical to the earlier record.
