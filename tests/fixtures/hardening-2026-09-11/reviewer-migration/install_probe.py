"""Inspect retained Install artifacts independently in ancestor-free scratch."""
from pathlib import Path
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / 'tests/fixtures/install-observation/after-install'
with tempfile.TemporaryDirectory(prefix='review-install-') as tmp:
    project = Path(tmp).resolve() / 'project'
    shutil.copytree(SOURCE, project)
    docs = project / 'docs'
    files = {p.name for p in docs.iterdir()}
    assert files == {'README.md', 'STATUS.md', 'CHANGELOG.md', 'DECISIONS.md'}, files
    readme = (docs / 'README.md').read_text()
    index = readme.split('## File index', 1)[1].split('\n---', 1)[0]
    assert set(re.findall(r'`([A-Z_-]+\.md)`', index)) == files, index
    for target in re.findall(r'\]\(([^)]+)\)', readme):
        if '://' not in target and not target.startswith('#'):
            assert (docs / target.split('#', 1)[0]).exists(), target
    status = (docs / 'STATUS.md').read_text()
    decisions = (docs / 'DECISIONS.md').read_text()
    log = (docs / 'CHANGELOG.md').read_text()
    assert not re.search(r'\[[^\]\n]+\]', status)
    assert not re.search(r'(?m)^##+ ', decisions)
    assert 'No decisions logged yet' in decisions
    assert 'YYYY-MM-DD' not in ''.join(p.read_text() for p in docs.iterdir())
    assert 'installed' in log.lower() and 'Seeded' in log
    assert (project / 'AGENTS.md').is_file()
    assert '## Project docs protocol' in (project / 'AGENTS.md').read_text()
    assert (project / 'check.py').read_bytes() == (SOURCE.parent / 'before-install/check.py').read_bytes()
    before = {str(p.relative_to(project)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in project.rglob('*') if p.is_file()}
    command = [sys.executable, '-B', str(ROOT / 'scripts/docs-doctor.py'), str(project),
               '--today', '2026-09-11', '--no-git']
    result = subprocess.run(command, capture_output=True, text=True)
    print('Doctor command:', command)
    print('Doctor exit:', result.returncode)
    print(result.stdout)
    print(result.stderr)
    assert result.returncode == 0
    assert before == {str(p.relative_to(project)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in project.rglob('*') if p.is_file()}
    print('INSTALL FIXTURE PASS: four docs, trimmed index and valid links, no STATUS/date residue,')
    print('empty decisions, separate AGENTS wiring, real install entry, unchanged source, read-only Doctor0')
