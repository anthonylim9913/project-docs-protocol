"""Disposable complete Git subjects for the real acceptance CLI tests."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'tests/fixtures/hardening-2026-09-12/acceptance-cases.json'


def invoke(root, *args):
    return subprocess.run([sys.executable, '-B', *map(str, args)], cwd=root,
                          capture_output=True, text=True, timeout=60)


def commit(root):
    subprocess.run(['git', 'add', '.'], cwd=root, check=True, capture_output=True)
    subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                    'commit', '--allow-empty', '-qm', 'Generated acceptance fixture'],
                   cwd=root, check=True, capture_output=True)
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()


def copy_subject(destination):
    shutil.copytree(ROOT, destination, ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc', '.tmp'))
    subprocess.run(['git', 'init', '-q'], cwd=destination, check=True)
    return commit(destination)


def generate(root, directory):
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    result_path = directory / 'result.json'
    process = invoke(root, 'tests/run_acceptance.py', '--runtime-root', root,
                     '--result', result_path, '--source-commit', head)
    if process.returncode:
        raise AssertionError(process.stdout + process.stderr + str(json.loads(result_path.read_text()).get('failures')))
    packet = json.loads(result_path.read_text())
    hashes = directory / 'hashes.json'
    # Scope comes from committed paths and this reviewed contract, never child output.
    paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', '-z', 'HEAD'], cwd=root, text=True).split('\0')
    docs = {'docs/README.md', 'docs/MIGRATION.md', 'docs/PROTOCOLS.md', 'docs/SKILL-REGISTRY.md',
            'docs/BRIEF-EXAMPLE.md', 'docs/EVIDENCE.md'}
    expected = {p for p in paths if p.startswith(('scripts/', 'templates/', 'tests/', 'staging/', '.github/'))
                or p in {'SKILL.md', 'AGENTS.md', 'CLAUDE.md', 'README.md', 'LICENSE'} | docs}
    import hashlib
    hashes.write_text(json.dumps({name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                                  for name in expected}))
    return packet, hashes


def validate(root, directory, packet, hashes):
    path = directory / 'validation.json'
    path.write_text(json.dumps(packet))
    return invoke(root, 'tests/validate_acceptance.py', path, MANIFEST, hashes)
