"""Independent source/ledger HTML boundary probes; scratch registers only."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / 'scripts/docs-migrate.py'
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('reviewed_migration', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
TODAY = '2026-09-11'

def snapshot(docs):
    return {p.name: p.read_bytes() for p in docs.iterdir() if p.is_file()}

def initialize(docs, source):
    docs.mkdir()
    for name, text in [('STATUS.md', '# STATUS\n\n## In flight\n' + source),
                       ('CHANGELOG.md', '# CHANGELOG\n\n## 2026-09-10 — previous work\n\nKeep history.\n'),
                       ('DECISIONS.md', '# DECISIONS\n')]:
        (docs / name).write_text(text)

def review(plan):
    for item in plan['mappings']:
        if not item['existing']:
            item['reviewed'] = True
            item['row']['closes_when'] = 'The parser acceptance fixture passes.'
    for item in plan['unmapped']:
        item.update(disposition='context', reason='HTML example scaffolding, not current work.')

print('script_sha256', hashlib.sha256(SCRIPT.read_bytes()).hexdigest())
examples = {
    'void_no_blank': '<br>\n',
    'paired_closed_no_blank': '<div></div>\n',
    'self_closing_no_blank': '<div/>\n',
}

for name, opening in examples.items():
    closing = ''
    source = opening + '| Item | Notes |\n|---|---|\n| Example parser | demo |\n' + closing + '\n- Actual finding.\n'
    with tempfile.TemporaryDirectory(prefix='review-html-') as tmp:
        project = Path(tmp).resolve()
        docs = project / 'docs'
        initialize(docs, source)
        plan = m.build_plan(docs, TODAY)
        print(name, 'source', json.dumps(source))
        print(name, 'mappings', json.dumps([item['source']['text'] for item in plan['mappings']]))
        print(name, 'unmapped', json.dumps([item['source']['text'] for item in plan['unmapped']]))
        review(plan)
        plan_path = project / 'reviewed.json'
        plan_path.write_text(json.dumps(plan))
        status_before = (docs / 'STATUS.md').read_bytes()
        command = [sys.executable, '-B', str(SCRIPT), str(project), '--today', TODAY,
                   '--plan', str(plan_path), '--write']
        result = subprocess.run(command, capture_output=True, text=True)
        print(name, 'command', json.dumps(command))
        print(name, 'exit', result.returncode, 'stderr', repr(result.stderr))
        assert result.returncode == 0, result.stderr
        assert status_before == (docs / 'STATUS.md').read_bytes()
        print(name, 'written_rows', json.dumps([line for line in (docs / 'LEDGER.md').read_text().splitlines()
                                              if 'migration:STATUS.md#' in line]))
        first = snapshot(docs)
        replay = subprocess.run(command, capture_output=True, text=True)
        assert replay.returncode == 0 and first == snapshot(docs)
        fresh = m.build_plan(docs, TODAY)
        assert fresh['counts']['new_rows'] == 0
        m.apply_plan(docs, fresh, TODAY)
        assert first == snapshot(docs)
        print(name, 'source_preservation_and_same_fresh_plan_idempotence', 'PASS')
        log = (docs / 'CHANGELOG.md').read_text()
        assert '\n## Findings\n' not in log

for name, opening in examples.items():
    closing = ''
    with tempfile.TemporaryDirectory(prefix='review-html-target-') as tmp:
        docs = Path(tmp).resolve() / 'docs'
        initialize(docs, '- Actual finding.\n')
        source = '# LEDGER\n' + opening + m.HEADER + closing
        (docs / 'LEDGER.md').write_text(source)
        before = snapshot(docs)
        try:
            plan = m.build_plan(docs, TODAY)
            review(plan)
            m.apply_plan(docs, plan, TODAY)
        except ValueError as exc:
            assert before == snapshot(docs)
            print(name, 'html_only_ledger_target', 'REFUSED', str(exc))
        else:
            print(name, 'html_only_ledger_target', 'ACCEPTED', json.dumps((docs / 'LEDGER.md').read_text()))
