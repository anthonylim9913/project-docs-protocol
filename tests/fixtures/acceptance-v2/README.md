# Canonical acceptance evidence schema 2

The original hand-authored four-case manifest and fixture bytes in
`hardening-2026-09-12/` are preserved. Schema 2 strengthens the evidence contract
without changing those runtime expectations. The public validator always selects
this schema; a packet cannot select a weaker mode.

Each case records structured command argv, ordered stage identities/exits and raw
stdout/stderr, plus complete before/after file hashes. Duplicate aggregate output
fields are forbidden. Controls have exact identities and the same observations.
The validator derives unauthorized additions/deletions and protected equality
from snapshots, checks fixture input bytes, actual diagnostic lines, plan input
hashes and the hand-declared source inventories. Synthetic reason keywords and
`passed`/`unchanged` flags cannot substitute for observations.

The old runner's purported “contiguous CDATA/PI” control actually exercised only
the generic migration-20 fixture. Schema 2 retains that useful write control under
`migration-20-safe-write` and adds genuine delimiter controls. Each contiguous
fixture has an active Findings section, one opaque record, and one visible
`Actual finding.` after the terminator: two source records, one unmapped opaque
record, one mapped row. Split fixtures still produce one unresolved opaque record
and refuse writing before journal creation. Generic migration still maps and
writes twenty findings, retaining its complete journal and unchanged STATUS.
These inventories were specified from literal fixtures; they are not regenerated
from child results or a new parser oracle.

`tests/input_manifest.py` selects all instructions/wiring at the root, every
script/template/test/staged-companion/CI file, and enumerated behavioral guidance
under docs, including the worked Brief, migration guide, registry, owner commands
and acceptance contracts. Tracked missing inputs and untracked additions are
visible; linked inputs, ignored untracked behavior, invalid portable paths and
dirty behavior are refused. Required core/template/fixture paths cannot disappear.
The tree digest hashes UTF-8 records `path:sha256\n` in lexicographic path order.

Generate behavior manifests only outside the reviewed checkout. Later execution
logs, review receipts, evidence manifests and handoffs are separate artifacts.
The behavior scope is not a blanket `docs/**` reporting allowance: Stage D/G
must enumerate permitted reporting changes and independently review their final
containing commit. Hashes and schema consistency do not prove genuine execution,
semantic source truth or independent review; raw runs and actual reviewers supply
those separate observations.

The old strict tests with fabricated Git identity never established targeted
rejection. They are replaced by real CLI controls in `test_acceptance_cli.py` and
`test_input_manifest_cli.py`. Generic nonstrict helper tests remain labeled as
helper coverage. `test_acceptance_guard_removal.py` first runs the named regression
intact, commits a single disabled guard in a disposable full subject, and requires
that regression to fail specifically because malformed output was accepted.

## Independent review corrections

Stage B review of `84f7cd0` returned FAIL with B-01–B-05 despite passing tests.
The revised input contract includes the delegated execution brief, source audit
and implementation plan as normative inputs. It compares working bytes directly
with HEAD blobs; Git status and index flags cannot certify different bytes under
the old identity. External manifest output uses a unique temporary file and
atomic replacement, and refuses preexisting symlink, hard-link and special-file
aliases.

Doctor reports must contain exactly the declared fixture check identities and
statuses, and one summary whose counts and exit agree. Descriptive informational
values remain variable. Migration evidence validates complete row fields and
flags, journal schema, every ledger cell/provenance, unchanged template/archive
contents and the exact new CHANGELOG mapping before preserved history. New tests
reproduce each independent counterexample, updating derived hashes to isolate the
semantic mutation. The diagnostic guard-removal case now targets the sole
summary guard, because complete-check validation also rejects keyword-only
output. Additional guard removals cover immutable blob binding, journal schema
and ledger row semantics.

The second independent review found that matched-row counting ignored malformed
extra Doctor diagnostics, and journal target objects accepted unsupported keys.
Doctor validation now accounts for every nonblank line, including its declared
scope notice; syntactic line coverage is separate from semantic summary counts.
Journal targets contain exactly `content` and `after`, matching the unchanged
writer replay contract. Additional valid-first and guard-removal regressions
cover both gaps, including indented/unrecognized diagnostics.

The numeric summary starts its own line. Descriptive check prose may include
`checks:` or a complete quoted summary without becoming another summary record.
The Stage B positive-preservation repair anchors summary selection while retaining
exact counts, exits, duplicate-summary rejection and full nonblank line coverage.
