# Independent skill-use observations

`observations.json` retains the exact inputs and final file contents from one
independent agent applying the working skill on 2026-09-10 to four isolated
projects. The evaluator received the skill, these raw inputs and each request;
it did not receive expected answers or the authored lifecycle tests.

The primary session then checked the resulting files: historical CHANGELOG
content remains intact; mixed and method-only replies create no fabricated
DECISIONS; the unanswered deployment question stays byte-identical; only the
resolved gate is removed; recovery preserves prior decision bytes and adds
D-0002 and D-0003 exactly once; the conflicting case has no file changes.
The evaluator also reported a repeated recovery check with no additional
writes. These snapshots establish final state, not a filesystem timing trace.

To repeat the exercise, restore each case's `before` files to a fresh isolated
project, provide an agent with the current skill and that case's request, then
compare its resulting artifacts with the stated invariants. Use only disposable
local fixture projects. This requires an agent and is separate from deterministic
`unittest` execution: loading saved output is not a fresh skill-use run.

This is four observations in one agent run, not four independent reviewers,
a stress-test population or an estimate of compliance across models. The
conflict is intentional test input and is not an unresolved project finding.
