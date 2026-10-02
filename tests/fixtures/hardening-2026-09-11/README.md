# September 11 continuation evidence

This directory records bounded, invented fixtures for the continuation from
`328105fcbeada838284096bb883efb44907570a9`. It contains no population survey or
inputs from unrelated private projects. The historical 28-register comparison
has no retained detailed artifacts and is not acceptance evidence here.

Reproduce the original-defect comparison without changing any Git refs:

```sh
python3 -B tests/compare_hardening_baseline.py
```

The runner exports that exact tracked commit into ignored temporary storage,
copies the four new test modules and parser snapshot into it, and executes the
same tests against old and current code. `baseline-comparison.json` records
the date, runtime, input test and source hashes, failure details, actual method
counts, skips and exit codes. Expected red subtest failures are distinct from
test-method counts; loader/runtime errors are not counted as reproduced bugs.
The current side must pass. Re-running intentionally refreshes this generated
comparison record; its hashes identify the input state.

Two defects were introduced and caught during this repair, so their affected
pre-fix state is intermediate code rather than the starting commit. The
[Markdown oracle evidence](../markdown-oracle/README.md) retains the ordered
sibling failure and repair, with an independent 1,098-wrapper sweep, 15 full
CLI probes and a discovery/replay matrix. `reviewer-migration/` retains actual
reviewed-write and hidden-target HTML containment probes and their original
and final outputs. Every such output identifies its script revision by hash.

The [fresh-context installation exercise](../install-observation/README.md)
retains two separate contexts, dispatched prompts, before/after snapshots and
explicitly condensed agent reports. It is an observed exercise, not an
automated compliance test. Standard `test_lifecycle.py` cases remain authored
artifact replays. All of these evidence forms have different limits and are
reported separately in [the hardening review](../../../docs/HARDENING-REVIEW.md).

Final acceptance commands and observed results are retained in
`verification.json` and the corresponding unittest/Doctor output files. The
normal suite and shipped tools use only the standard library. The pinned
Markdown parser and PyYAML validator dependency exist only in ignored local
development storage; neither is a shipped runtime dependency.
