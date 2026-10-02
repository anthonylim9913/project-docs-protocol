"""Independent complete-Install CLI probes; development parser required."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[4]
DOCTOR = ROOT / 'scripts/docs-doctor.py'
BLOCK = (ROOT / 'SKILL.md').read_text().split('### Step 2', 1)[1].split('```markdown', 1)[1].split('```', 1)[0].strip('\n').replace('<docs-path>', 'docs') + '\n'
TIGHT = '\n'.join(line for line in BLOCK.splitlines() if line.strip()) + '\n'


def indent(source, n):
    return '\n'.join(' ' * n + line if line.strip() else '' for line in source.splitlines()) + '\n'


cases = {
    'nested-six-space-live': '- Outer\n    - Inner\n\n' + indent(BLOCK, 6),
    'nested-plus': '+ Outer\n    + Inner\n\n' + indent(BLOCK, 6),
    'nested-star': '* Outer\n    * Inner\n\n' + indent(BLOCK, 6),
    'nested-numbered': '1. Outer\n\n   2. Inner\n\n' + indent(BLOCK, 6),
    'numbered-six-space-continuation': '1. Outer\n\n' + indent(BLOCK, 6),
    'tab-padding': '-\tOuter\n\t-\tInner\n\n' + '\n'.join('\t\t' + line if line.strip() else '' for line in BLOCK.splitlines()) + '\n',
    'extra-blank': '- Outer\n\n    - Inner\n\n\n' + indent(BLOCK, 6),
    'tight-heading': '- Outer\n    - Inner\n' + indent(BLOCK, 6),
    'lazy-top-level': 'Active instructions:\n' + indent(TIGHT, 4),
    'lazy-nested': '- Outer\n    - Active instructions:\n' + indent(TIGHT, 10),
    'top-level-code': 'Example:\n\n' + indent(BLOCK, 4),
    'top-level-tab-code': 'Example:\n\n' + '\n'.join('\t' + line if line.strip() else '' for line in BLOCK.splitlines()) + '\n',
    'marker-surplus-tight': '-     ' + TIGHT.splitlines()[0] + '\n' + indent('\n'.join(TIGHT.splitlines()[1:]), 6),
    'ordered-sibling-four-space-code': '1. Outer\n  2. Inner\n\n' + indent(BLOCK, 4),
    'ordered-sibling-seven-space-live': '1. Outer\n  2. Inner\n\n' + indent(BLOCK, 7),
}
assert importlib.metadata.version('markdown-it-py') == '4.0.0'
parser = MarkdownIt('commonmark')
observations = []
for name, source in cases.items():
    live = any(token.type == 'inline' and 'This project uses the project-docs-protocol' in token.content for token in parser.parse(source))
    with tempfile.TemporaryDirectory(prefix='independent-doctor-cli-') as temporary:
        project = Path(temporary)
        docs = project / 'docs'
        docs.mkdir()
        (project / 'AGENTS.md').write_text(source)
        for filename, body in {
            'STATUS.md': '# STATUS\n\nLast updated: 2026-09-11\n\n## Current phase\n\nIndependent review.\n',
            'CHANGELOG.md': '# CHANGELOG\n\n## 2026-09-11 — initialized project documentation system\n\nInstalled.\n',
            'DECISIONS.md': '# DECISIONS\n',
            'README.md': '*Installed via the `project-docs-protocol` skill.*\n',
        }.items():
            (docs / filename).write_text(body)
        snapshot = lambda: {str(p.relative_to(project)): p.read_bytes() for p in project.rglob('*') if p.is_file()}
        before = snapshot()
        result = subprocess.run([sys.executable, '-B', str(DOCTOR), str(project), '--today', '2026-09-11', '--no-git'], text=True, capture_output=True, timeout=15)
        checks = {check: level for level, check in re.findall(r'^(PASS|WARN|FAIL|SKIP)\s+(wiring-\S+)', result.stdout, re.M)}
        expected = ['PASS', 'PASS', 'PASS'] if live else ['FAIL', 'SKIP', 'SKIP']
        assert [checks.get(k) for k in ['wiring-block', 'wiring-clauses', 'wiring-path']] == expected, (name, result.stdout, result.stderr)
        assert result.returncode == (0 if live else 2), (name, result.stdout, result.stderr)
        assert not result.stderr and 'git-status-churn' in result.stdout
        assert before == snapshot()
        observations.append({'name': name, 'source': source, 'oracle_live': live, 'doctor_exit': result.returncode, 'wiring_checks': checks, 'later_checks_completed': True, 'project_bytes_unchanged': True})
print(json.dumps({'parser': 'markdown-it-py 4.0.0; commonmark preset', 'doctor_script_sha256': hashlib.sha256(DOCTOR.read_bytes()).hexdigest(), 'cases': observations}, indent=2))
