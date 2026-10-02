"""Complete behavior input scope, separate from generated release evidence.

A tree digest is SHA256 of UTF-8 sorted `path:sha256\n` records. Paths are
POSIX relative paths; colons/newlines are forbidden. The manifest never hashes
itself: it is generated outside this scope after the behavior subject freezes.
"""
from pathlib import Path, PurePosixPath
import hashlib
import json
import os
import stat
import tempfile
import re
import subprocess

ROOT_FILES = {'SKILL.md', 'AGENTS.md', 'CLAUDE.md', 'README.md', 'LICENSE'}
DIRECTORIES = ('scripts/', 'templates/', 'tests/', 'staging/', '.github/')
DOC_INPUTS = {'docs/README.md', 'docs/MIGRATION.md', 'docs/PROTOCOLS.md', 'docs/SKILL-REGISTRY.md',
              'docs/BRIEF-EXAMPLE.md', 'docs/EVIDENCE.md'}
REQUIRED = ROOT_FILES | DOC_INPUTS | {
    'scripts/docs-doctor.py', 'scripts/docs-migrate.py', 'scripts/register_paths.py',
    'scripts/skill-registry.py', 'tests/run_acceptance.py', 'tests/acceptance_gate.py',
    'tests/validate_acceptance.py', 'tests/input_manifest.py', 'tests/acceptance_evidence.py',
    'tests/fixtures/acceptance-v2/contiguous-cdata.md', 'tests/fixtures/acceptance-v2/contiguous-pi.md',
    'tests/fixtures/migration-20/STATUS.md',
    'tests/fixtures/hardening-2026-09-12/acceptance-cases.json',
    'tests/fixtures/acceptance-v2/contract.json',
    'staging/architect-protocol/scripts/architect_packet.py', 'staging/architect-protocol/SCHEMA.md',
    'staging/research-protocol/SKILL.md', 'staging/architect-protocol/SKILL.md',
} | {'templates/' + n for n in ('README.md', 'STATUS.md', 'CHANGELOG.md', 'DECISIONS.md', 'LEDGER.md')}


def valid_path(value):
    return (isinstance(value, str) and bool(value) and not any(c in value for c in '\\:\n\r\0')
            and not PurePosixPath(value).is_absolute()
            and all(p not in ('', '.', '..') for p in value.split('/')))


def in_scope(name):
    if '__pycache__' in name.split('/') or name.endswith('.pyc') or name.startswith('tests/.tmp/'):
        return False
    selected = name in ROOT_FILES | DOC_INPUTS or name.startswith(DIRECTORIES)
    if selected and not valid_path(name):
        raise ValueError('unsupported behavior input path: ' + repr(name))
    return selected


def required_paths(root):
    tracked = subprocess.check_output(['git', '-C', str(root), 'ls-tree', '-r', '--name-only', '-z', 'HEAD'], text=True).split('\0')
    present = [p.relative_to(root).as_posix() for prefix in DIRECTORIES
               for p in (root / prefix).rglob('*') if p.is_file() or p.is_symlink()]
    paths = REQUIRED | {p for p in tracked + present if in_scope(p)}
    for name in sorted(paths):
        path = root / name
        if not path.is_file() or any(p.is_symlink() for p in [path] + list(path.parents) if p != root and root in p.parents):
            raise ValueError('required input missing or linked: ' + name)
    return paths


def committed_hashes(root, names):
    """Read immutable HEAD blob bytes; index flags cannot suppress this check."""
    names = sorted(names)
    requests = ''.join('HEAD:' + name + '\n' for name in names).encode('utf-8')
    raw = subprocess.check_output(['git', '-C', str(root), 'cat-file', '--batch'], input=requests)
    values = {}
    offset = 0
    for name in names:
        end = raw.index(b'\n', offset)
        header = raw[offset:end].split()
        if len(header) != 3 or header[1] != b'blob':
            raise ValueError('behavior input is not committed: ' + name)
        size = int(header[2])
        start = end + 1
        content = raw[start:start + size]
        if len(content) != size or raw[start + size:start + size + 1] != b'\n':
            raise ValueError('malformed Git blob response')
        values[name] = hashlib.sha256(content).hexdigest()
        offset = start + size + 1
    return values


def dirty_inputs(root):
    """NUL-separated paths include both sides of renames and untracked files."""
    modified = subprocess.check_output(['git', '-C', str(root), 'diff', '--name-only',
                                        '--no-renames', '-z', 'HEAD'], text=True)
    untracked = subprocess.check_output(['git', '-C', str(root), 'ls-files', '--others',
                                        '-z'], text=True)
    dirty = {p for p in (modified + untracked).split('\0') if in_scope(p)}
    current = hashes(root)
    # Untracked paths already fail; avoid requesting a nonexistent HEAD blob.
    if not dirty:
        committed = committed_hashes(root, current)
        dirty.update(p for p in current if current[p] != committed[p])
    return sorted(dirty)


def hashes(root):
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in sorted(required_paths(root))}


def tree_hash(values):
    if not isinstance(values, dict) or any(not valid_path(k) or not isinstance(v, str) or
            not re.fullmatch('[0-9a-f]{64}', v) for k, v in values.items()):
        raise ValueError('invalid input hash map')
    return hashlib.sha256((''.join(k + ':' + values[k] + '\n' for k in sorted(values))).encode()).hexdigest()


def main():
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path); p.add_argument('--out', type=Path, required=True)
    a = p.parse_args(); root = a.root.resolve()
    if root == a.out.resolve() or root in a.out.resolve().parents:
        p.error('input manifest output must be outside the reviewed tree')
    try:
        if a.out.exists() or a.out.is_symlink():
            metadata = a.out.lstat()
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                p.error('output must be a regular unlinked file')
        if dirty_inputs(root):
            p.error('behavior inputs must be clean before manifest generation')
        values = hashes(root)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        p.error(str(error))
    result = {'schema': 1, 'kind': 'behavior-inputs', 'subject_commit': subprocess.check_output(
        ['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
        'files': values, 'tree_sha256': tree_hash(values)}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.input-manifest-', dir=str(a.out.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(json.dumps(result, indent=2, sort_keys=True) + '\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, a.out)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


if __name__ == '__main__':
    main()
