"""Disposable complete Git subjects for the real acceptance CLI tests."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REVIEWED_EXCLUSIONS = {'docs/STATUS.md', 'docs/CHANGELOG.md', 'docs/DECISIONS.md', 'docs/LEDGER.md',
                       'docs/LEDGER-ARCHIVE.md', 'docs/HARDENING-REVIEW.md', 'docs/LESSONS-REVIEW.md'}
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
    shutil.copytree(ROOT, destination, ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc', '.tmp', '.DS_Store'))
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
    # Independent restatement of the binding rule: every tracked file except the reviewed
    # exclusions. Deliberately not imported from input_manifest so the two can disagree.
    expected = {p for p in paths if p and p not in REVIEWED_EXCLUSIONS}
    import hashlib
    hashes.write_text(json.dumps({name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                                  for name in expected}))
    return packet, hashes


def validate(root, directory, packet, hashes):
    path = directory / 'validation.json'
    path.write_text(json.dumps(packet))
    return invoke(root, 'tests/validate_acceptance.py', path, MANIFEST, hashes)


def isolated(root, *args):
    """Run a judging entry point the way a reviewer does: `python3 -I -B`, from its own checkout."""
    return subprocess.run([sys.executable, '-I', '-B', *map(str, args)], cwd=root,
                          capture_output=True, text=True, timeout=60)


def external(trusted, candidate, directory, *pin):
    """The external check: the trusted checkout's runner and validator judge `candidate`.

    Returns (runner process, validator process). The candidate's code is executed only as
    the product under test (its scripts/), never as judging code.
    """
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=candidate, text=True).strip()
    result = directory / 'external-result.json'
    if result.exists():
        result.unlink()
    runner = isolated(trusted, 'tests/run_acceptance.py', '--runtime-root', candidate,
                      '--result', result, '--source-commit', head, *pin)
    paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', '-z', 'HEAD'], cwd=candidate, text=True).split('\0')
    import hashlib
    hashes = directory / 'external-hashes.json'
    hashes.write_text(json.dumps({name: hashlib.sha256((candidate / name).read_bytes()).hexdigest()
                                  for name in paths if name and name not in REVIEWED_EXCLUSIONS}))
    if not result.exists():
        result.write_text('{}')
    validator = isolated(trusted, 'tests/validate_acceptance.py', *pin, '--subject-root', candidate,
                         result, MANIFEST, hashes)
    return runner, validator
