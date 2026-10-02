# Independent migration and installation review

Completed exact-code review of the working diff from `328105fcbeada838284096bb883efb44907570a9`, including the final migration script, its shared target selection, `docs/MIGRATION.md`, migration tests, and the four-document Install instructions, templates, tests and retained Install fixture. No tracked implementation files or project registers were edited by this reviewer. Scratch projects were temporary; the files here are review evidence.

The final reviewed `scripts/docs-migrate.py` SHA-256 is `dff2647f5e4594abaaff8d38f21791d421add7e1fb64d2247f73bc3e43c92d88`. Shared `scripts/register_paths.py` is `f8ee7ba8bacd1404d9475e08108c94a5638befb6ea7d80d44f26d8deef1948b3`. The script hash was checked before and after the final runs. Target selection, plan generation/validation, journal validation/replay, target binding, apply and CLI function ASTs were unchanged between the initially reviewed script and the final HTML repair; their original diff and final behavior were reviewed.

## Finding resolved during review

One HTML containment finding had four trigger families. Paired tag-shaped text inside comments or quoted attributes, incomplete multiline void tags, adjacent same-line element roots, and completed nonraw tags without a following blank line could release pipe examples as live findings. Actual reviewed CLI writes created bogus OPEN rows. The same boundaries allowed an HTML-only ledger example to become the write target. The final scanner preserves all these contents for reconciliation, using lexical state and explicit open elements; nonraw blocks also require a blank separator after completion.

The red artifacts are intermediate implementation results, not an assertion that all variants were introduced by the starting commit:

| Trigger family | Red script SHA-256 | Red output | Final output |
|---|---|---|---|
| Paired comment/quoted attribute, plus nested/pre controls | `1ef52953480a1a621ce8a0bfa19cadfd4190aaa9cdbb07e83e8db8e69bacf94d` | `html_boundary_probe.txt` | `html_boundary_green.txt` |
| Multiline img/br/input attributes | `98bd427fdeb533647b62311f9ebf8a6d820075b82101f56713ab83376c806794` | `void_boundary_red.txt` | `void_boundary_green.txt` |
| Adjacent div/pre or div/div roots | `3362ee5cfb8dc10d80b4f9128d0dfb7b6cc3377ab9693d51102a3fb6ccc46340` | `adjacent_boundary_red.txt` | `adjacent_boundary_green.txt` |
| No blank after br, closed div or self-closing div | `d2d6fbc2b3881d2d76d6c84f2ac52939fe82328970b9473acfceeb9fb76a8bdb` | `blank_boundary_red.txt` | `blank_boundary_green.txt` |

All 13 final HTML cases performed actual reviewed CLI writes with only the real finding, refused their corresponding hidden-only ledger targets, preserved STATUS bytes, and passed same-plan and fresh-plan byte-idempotence checks. The three no-blank boundaries were independently compared with markdown-it-py 4.0.0; all no-blank tables were opaque, and all blank-separated controls were live. That development-only oracle is retained separately and is not a runtime dependency or a claim of general Markdown conformance.

## Final verification

Commands below ran from the repository root. All returned exit 0. The four boundary probes print their observed mappings and target outcomes; the reviewer additionally checked that every final written row omitted `Example parser` and every hidden-only target reported `REFUSED`.

```sh
python3 -B tests/fixtures/hardening-2026-09-11/reviewer-migration/html_boundary_probe.py
python3 -B tests/fixtures/hardening-2026-09-11/reviewer-migration/void_boundary_probe.py
python3 -B tests/fixtures/hardening-2026-09-11/reviewer-migration/adjacent_boundary_probe.py
python3 -B tests/fixtures/hardening-2026-09-11/reviewer-migration/blank_boundary_probe.py
python3 -B tests/fixtures/hardening-2026-09-11/reviewer-migration/core_probe.py
python3 -B tests/fixtures/hardening-2026-09-11/reviewer-migration/install_probe.py
python3 -B -m unittest -v tests.test_migrate tests.test_migrate_semantics tests.test_installation tests.test_register_selection
git diff --check
```

`regression.txt` records 82 passing tests. `core_probe.txt` records independent actual-write checks for A (secondary owner sign-off), B (conflicting OPEN/BLOCKED aliases refused, then source reconciled and replanned), C (provider quota and owner approval both retained), all five gate aliases, removal of every gate refused, unknown formatted state unresolved, ordinary-title/custom-table positive controls, quoted multiline source in CHANGELOG, review/empty-closing-condition/old-unbound-plan/redirect/stale-plan refusals, interrupted log-first write recovery, recovery target binding, source preservation and exactly-once replay.

`install_probe.txt` records independent inspection of the retained after-install artifacts copied to ancestor-free temporary storage: four documentation files, no dangling optional file-index entries or local links, no STATUS/date residue, empty DECISIONS, separate AGENTS wiring, an installation entry consistent with the retained source, and unchanged source bytes. Doctor reported 22 checks: 16 pass, zero warn, zero fail, three info, three skipped; exit 0. This is artifact verification, not an additional agent installation observation or a general compliance rate.

The optional independent oracle was run with:

```sh
tests/.tmp/markdown-oracle-venv/bin/python -B tests/fixtures/hardening-2026-09-11/reviewer-migration/blank_boundary_oracle.py
```

## Evidence handling and limits

Retained text outputs are **normalized transcripts**, not raw logs: repository paths are `<repo>`, the Python executable is `<python>`, and generated system temporary project roots are `<scratch>`. Actual input text, hashes, row contents, diagnostics and outcomes are unchanged. Probe programs retain the complete reproducible inputs and invoke the real CLI; projects are deleted by their temporary-directory cleanup.

No unresolved actionable defect remains in this review scope on the exact final script. Rejected candidates include formatted state-looking ordinary titles (intentionally OPEN), bespoke tables with no possible state (supported), a reviewer-supplied false context disposition (a documented human semantic responsibility), and raw element first-close behavior (explicit contract). The HTML scanner is conservative and bounded: it does not infer a DOM or implicit closing tags. These checks do not establish exhaustive Markdown conformance or the truth of arbitrary reviewed closing conditions.

The exact intermediate migration script before the lexical containment repair is retained as `before-containment-fix.py.txt`, SHA-256 `1ef52953480a1a621ce8a0bfa19cadfd4190aaa9cdbb07e83e8db8e69bacf94d`. The `.txt` suffix prevents accidental execution or discovery. To repeat its red behavior, copy this snapshot as `scripts/docs-migrate.py` in a disposable export of the implementation commit (with the shared helper and templates), then run the retained probe programs there. Do not replace the active installation. The probe outputs distinguish subsequent intermediate trigger variants by their recorded hashes; this first snapshot already exhibits their unsafe example mapping.
