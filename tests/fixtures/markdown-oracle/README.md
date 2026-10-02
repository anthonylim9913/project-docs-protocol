# Markdown visibility development oracle

`observations.json` retains 23 invented instruction documents built from the
complete Install Step 2 block in `SKILL.md`, plus the block tokens produced by
**markdown-it-py 4.0.0 with its `commonmark` preset**. `record_oracle.py` creates
that snapshot. Token `lines` are zero-based, end-exclusive source intervals.
`oracle_live` means the installation sentence occurs in an inline token rather
than a code block. The tokens also retain the complete clause text and nested
list structure for review. No private projects or paths are recorded.

The regular suite uses the standard library only. Four test methods execute
23 full Doctor CLI cases and check that the snapshot still covers the exact
current inputs. Each live case requires PASS for `wiring-block`,
`wiring-clauses` and `wiring-path`; code cases require FAIL/SKIP/SKIP. Every CLI
case checks the exit code, completion of later checks and unchanged project
bytes. The intentional ancestor-register advisory makes healthy scratch
projects exit 1; it is not suppressed.

The independent parser rejected one initial test expectation. With
`10. Outer section\n    20. Protocol section\n\n`, the `20.` line cannot start
a nested ordered list by interrupting an open paragraph: that interruption
requires a list beginning with `1`. The subsequent eight-space block is
code, so the retained `wide-numbered-cannot-interrupt-paragraph` case expects
no wiring. `nested-wide-numbered` uses a blank line before the nested marker
and is genuinely nested. The expectation was corrected before implementing
the visibility repair. All 23 retained expectations agree with the oracle.

A subsequent independent reviewer found that an ordered sibling can change
its marker indentation: `1. Outer\n  2. Inner\n\n` ends the first item and
starts its sibling with a content baseline of five columns. The full block at
four spaces therefore sits outside that item as code, while seven spaces is
live item content. The initial repair's exact-marker-column comparison
misclassified both directions. Two added CLI cases failed before the sibling
repair and now pass. The original starting script already passed these two;
their red evidence is the intermediate helper, not the starting commit.
The reviewer retained the original probe and independent results under
`reviewer-probes/`. Re-executing its 1,098 generated wrappers after repair
found zero visibility disagreements; this remains a bounded wrapper sweep.

`cli-observations.json` records the three wiring checks and exit code for
every case against the starting script at
`328105fcbeada838284096bb883efb44907570a9` and the repaired visibility filter.
Ten cases fail the intended contract on that starting script; the intermediate
`before_sibling_fix` state fails the two added sibling cases; all 23 pass with
the final repair. The intermediate and repaired hashes cover the visibility
helper region only, because discovery was being repaired independently in
the same script.

To reproduce the retained oracle locally (network is needed only to obtain
the development dependency, never to run the test suite):

```sh
python3 -m venv tests/.tmp/markdown-oracle-venv
tests/.tmp/markdown-oracle-venv/bin/python -m pip install markdown-it-py==4.0.0
tests/.tmp/markdown-oracle-venv/bin/python -B tests/fixtures/markdown-oracle/record_oracle.py
python3 -B -m unittest tests.test_doctor_markdown -v
```

For the red run, extract the script without altering the working tree:

```sh
git show 328105fc:scripts/docs-doctor.py > tests/.tmp/docs-doctor-328105fc.py
DOCS_DOCTOR_UNDER_TEST=tests/.tmp/docs-doctor-328105fc.py python3 -B -m unittest tests.test_doctor_markdown -v
```

This is bounded development evidence, not a claim of CommonMark or GFM
conformance. It covers nested bullet and numbered containers, tab stops,
blank lines, marker surplus indentation, fenced examples and lazy paragraph
continuation around this Install block. It does not test the CommonMark
specification corpus, every combination of blockquote and list nesting,
inline HTML block types, setext headings or GFM extensions. Doctor remains a
small visibility filter with a standard-library runtime; the oracle does not
establish semantic correctness of an installed protocol or agent compliance.

## Routing snapshot — 2026-09-22

The Stage E conditional-registry wiring adds one bullet to the complete Install
block. `observations-routing-20260922.json` is a new parser observation for all
29 current wrappers; the original `observations.json` remains byte-identical.
All case names and authored `live` expectations remain identical, checked by the
regular suite. Markdown-it-py 4.0.0 independently parsed the new text and agreed
with all 29 unchanged expectations. No Doctor output supplied the oracle. The
first integration run's sole failure was exact source-text identity against the
old snapshot; real CLI visibility expectations still passed. This is a fixture
input change for the new wiring, not a change to Markdown support or outcomes.

## Routing bullet removed — 2026-10-02

The generic routing bullet left the Install block (D-0020); a project with a
registry now adds a conditional line instead. The current block is again
byte-identical to the text `observations.json` was recorded against, so the
regular suite checks the current inputs against that recording.
`observations-routing-20260922.json` stays as the parser observation of the
2026-09-22 text; its case names and expectations are checked to match.

To recheck without changing tracked evidence, provide the snapshot as input and
a new external result path:

```sh
/path/to/oracle-venv/bin/python -B tests/fixtures/markdown-oracle/record_oracle.py \
  --snapshot tests/fixtures/markdown-oracle/observations.json \
  --out /absolute/external/oracle-observations.json
```
