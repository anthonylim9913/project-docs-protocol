"""Independent required-case CLI and protection probes; no tracked writes."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest import mock

ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / 'scripts/docs-migrate.py'
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('reviewed_migration', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
TODAY = '2026-09-11'


def snapshot(docs):
    return {p.relative_to(docs).as_posix(): p.read_bytes() for p in docs.rglob('*') if p.is_file()}


def init(docs, source):
    docs.mkdir()
    (docs / 'STATUS.md').write_bytes(('# STATUS\n\n## In flight\n\n' + source).encode())
    (docs / 'CHANGELOG.md').write_text('# CHANGELOG\n\n## 2026-09-10 — existing entry\n\nHistorical fact stays.\n')
    (docs / 'DECISIONS.md').write_text('# DECISIONS\n\nNo decisions logged yet.\n')


def reviewed(docs):
    plan = m.build_plan(docs, TODAY)
    for mapping in plan['mappings']:
        mapping['reviewed'] = True
        mapping['row']['closes_when'] = 'Running the parser acceptance fixture prints PASS.'
    return plan


def cli(docs, plan):
    p = docs.parent / 'reviewed.json'
    p.write_text(json.dumps(plan))
    return subprocess.run([sys.executable, '-B', str(SCRIPT), str(docs), '--today', TODAY,
                           '--plan', str(p), '--write'], capture_output=True, text=True)


def refuse(docs, plan, phrase):
    before = snapshot(docs)
    result = cli(docs, plan)
    assert result.returncode == 2 and phrase in result.stderr, (result.returncode, result.stderr)
    assert before == snapshot(docs)


def apply(docs, plan, validate=True):
    original = (docs / 'STATUS.md').read_bytes()
    if validate:
        m.validate_plan(docs, plan, TODAY)
    result = cli(docs, plan)
    assert result.returncode == 0, result.stderr
    assert original == (docs / 'STATUS.md').read_bytes()
    first = snapshot(docs)
    result = cli(docs, plan)
    assert result.returncode == 0 and snapshot(docs) == first
    fresh = m.build_plan(docs, TODAY)
    assert fresh['counts']['new_rows'] == 0
    m.apply_plan(docs, fresh, TODAY)
    assert snapshot(docs) == first
    return m.ledger_rows((docs / 'LEDGER.md').read_text(), 'LEDGER.md')


print('script_sha256', hashlib.sha256(SCRIPT.read_bytes()).hexdigest())
with tempfile.TemporaryDirectory(prefix='review-migration-core-') as tmp:
    base = Path(tmp).resolve()
    cases = [
        ('A', '| Item | Status | Blocked on | Gate |\n|---|---|---|---|\n| Ship parser | OPEN | | owner sign-off |\n', 'owner sign-off'),
        ('C', '| Item | Status | Blocked on | Blocked by |\n|---|---|---|---|\n| Ship parser | BLOCKED | provider quota | owner approval |\n', 'provider quota; owner approval'),
        ('all_aliases', '| Item | State | Blocked on | Blocked-on | Blocked by | Gate | Blocker |\n|---|---|---|---|---|---|---|\n| Ship parser | **OPEN** | quota | legal | owner | finance | test |\n', 'quota; legal; owner; finance; test'),
    ]
    for name, source, gate in cases:
        docs = base / name; init(docs, source)
        plan = reviewed(docs)
        row = plan['mappings'][0]['row']
        assert row['status'] == 'BLOCKED' and row['blocked_on'] == gate
        for omitted in gate.split('; '):
            modified = copy.deepcopy(plan)
            modified['mappings'][0]['row']['blocked_on'] = '; '.join(g for g in gate.split('; ') if g != omitted)
            if not modified['mappings'][0]['row']['blocked_on']:
                modified['mappings'][0]['row']['status'] = 'OPEN'
            refuse(docs, modified, 'source')
        rows = apply(docs, plan)
        assert len(rows) == 1 and rows[0][2] == 'BLOCKED' and rows[0][7] == gate
        print(name, 'PASS actual CLI write, every-gate validation, source bytes, same/fresh idempotence', rows[0][7])

    unresolved = {
        'B': '| Item | Status | State |\n|---|---|---|\n| Ship parser | OPEN | BLOCKED |\n',
        'unknown_state': '| Alpha | Beta | Gamma |\n|---|---|---|\n| Ship parser | **BLOCKED** | owner |\n',
    }
    for name, source in unresolved.items():
        docs = base / name; init(docs, source)
        plan = reviewed(docs)
        assert plan['counts']['new_rows'] == 0 and len(plan['unmapped']) == 1
        assert plan['unmapped'][0]['source']['text'] == source.splitlines()[-1]
        refuse(docs, plan, 'disposition')
        print(name, 'PASS unresolved complete row, CLI refusal with no writes')
        if name == 'B':
            (docs / 'STATUS.md').write_text('# STATUS\n## In flight\n| Item | Status | Gate |\n|---|---|---|\n| Ship parser | BLOCKED | owner approval |\n')
            refuse(docs, plan, 'changed')
            rows = apply(docs, reviewed(docs))
            assert rows[0][2] == 'BLOCKED' and rows[0][7] == 'owner approval'
            print('B', 'PASS requires fresh source reconciliation then gated write')

    docs = base / 'positive'; init(docs, '| Item | Notes |\n|---|---|\n| **BLOCKED** | title is ordinary work |\n| requests blocked by CORS | ordinary title |\n\n| Alpha | Beta | Gamma |\n|---|---|---|\n| Ship parser | today | web/ |\n')
    plan = reviewed(docs)
    assert len(plan['mappings']) == 3 and not plan['unmapped']
    rows = apply(docs, plan)
    assert len(rows) == 3 and all(row[2] == 'OPEN' for row in rows)
    print('positive_controls PASS ordinary titles and bespoke no-state table write')

    docs = base / 'html_log'
    example = '<pre>\n## 2026-09-11 — fabricated completed work\n| Item | State |\n|---|---|\n| Example parser | OPEN |\n</pre>'
    init(docs, example + '\n\n- Actual finding.\n')
    plan = reviewed(docs)
    assert len(plan['mappings']) == 1 and len(plan['unmapped']) == 1
    assert plan['unmapped'][0]['source']['text'] == example
    refuse(docs, plan, 'disposition')
    plan['unmapped'][0].update(disposition='context', reason='Only an illustrative code example.')
    rows = apply(docs, plan)
    assert len(rows) == 1 and 'Actual finding' in rows[0][4]
    log = (docs / 'CHANGELOG.md').read_text()
    assert '\n## 2026-09-11 — fabricated completed work\n' not in log
    assert json.dumps(example, ensure_ascii=False) in log
    print('html_log PASS exact multiline source quoted in log; only real finding written')

    docs = base / 'protect'; init(docs, '- Ship parser.\n')
    plan = reviewed(docs)
    for field, value, phrase in [('reviewed', False, 'review')]:
        changed = copy.deepcopy(plan); changed['mappings'][0][field] = value
        refuse(docs, changed, phrase)
    changed = copy.deepcopy(plan); changed['mappings'][0]['row']['closes_when'] = ''
    refuse(docs, changed, 'real reviewed')
    changed = copy.deepcopy(plan); changed.pop('register_dir')
    refuse(docs, changed, 'target')
    clone = base / 'clone'; shutil.copytree(docs, clone)
    refuse(clone, plan, 'target')
    (docs / 'CHANGELOG.md').write_text((docs / 'CHANGELOG.md').read_text() + 'New entry invalidates review.\n')
    refuse(docs, plan, 'changed')
    print('protections PASS unreviewed/empty-close/old-unbound-plan/redirect/stale refusal, bytes unchanged')

    docs = base / 'recovery'; init(docs, '- Ship parser.\n')
    plan = reviewed(docs)
    original_write = m.atomic_write
    def interrupt(path, content):
        original_write(path, content)
        if path.name == 'CHANGELOG.md':
            raise OSError('independent interruption after log')
    try:
        with mock.patch.object(m, 'atomic_write', side_effect=interrupt):
            m.apply_plan(docs, plan, TODAY)
    except OSError:
        pass
    else:
        raise AssertionError('fault did not fire')
    assert (docs / m.JOURNAL).exists() and not (docs / 'LEDGER.md').exists()
    clone = base / 'recovery_clone'; shutil.copytree(docs, clone)
    refuse(clone, plan, 'target')
    rows = apply(docs, plan, validate=False)
    assert len(rows) == 1
    assert (docs / 'CHANGELOG.md').read_text().count('reviewed STATUS-to-LEDGER migration') == 1
    print('recovery PASS log-first interruption, replay target binding, exactly-once log/row and source preservation')
print('ALL INDEPENDENT CORE PROBES PASS')
