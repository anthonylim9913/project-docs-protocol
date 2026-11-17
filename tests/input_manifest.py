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

EXCLUDED = frozenset({
    'docs/STATUS.md', 'docs/CHANGELOG.md', 'docs/DECISIONS.md', 'docs/LEDGER.md',
    'docs/LEDGER-ARCHIVE.md',
    'docs/HARDENING-REVIEW.md', 'docs/LESSONS-REVIEW.md',
})
EXCLUDED_DIRECTORIES = ('.git/', 'tests/.tmp/')
SKIPPED_BASENAMES = frozenset({'.DS_Store'})
BYTECODE_SUFFIXES = ('.pyc', '.pyo', '.so', '.pyd', '.pth')
ROOT_FILES = {'SKILL.md', 'AGENTS.md', 'CLAUDE.md', 'README.md', 'LICENSE'}
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


def git(root, *arguments, **kwargs):
    """Refuse failed or stderr-producing Git operations, including warnings."""
    result = subprocess.run(['git', '-C', str(root), *arguments], capture_output=True, **kwargs)
    if result.returncode or result.stderr:
        diagnostic = result.stderr
        if isinstance(diagnostic, bytes):
            diagnostic = diagnostic.decode('utf-8', errors='replace')
        raise ValueError('git ' + arguments[0] + ' failed (exit ' + str(result.returncode) + '): ' + diagnostic.strip())
    return result.stdout


def valid_path(value):
    return (isinstance(value, str) and bool(value) and not any(c in value for c in '\\:\n\r\0')
            and not PurePosixPath(value).is_absolute()
            and all(p not in ('', '.', '..') for p in value.split('/')))


def in_scope(name):
    if not name or name.rsplit('/', 1)[-1] in SKIPPED_BASENAMES:
        return False
    if name in EXCLUDED or name == '.git' or name.startswith(EXCLUDED_DIRECTORIES):
        return False
    if '__pycache__' in name.split('/') or name.endswith(BYTECODE_SUFFIXES):
        raise ValueError('bytecode or import hook in the reviewed tree (remove it): ' + name)
    if not valid_path(name):
        raise ValueError('unsupported behavior input path: ' + repr(name))
    return True


def present_paths(root):
    """Files and links on disk; linked directories are reported, never followed."""
    found = []

    def cannot_enumerate(error):
        raise ValueError('cannot enumerate: ' + str(error.filename)) from error

    for base, directories, files in os.walk(root, onerror=cannot_enumerate):
        relative = Path(base).relative_to(root).as_posix()
        prefix = '' if relative == '.' else relative + '/'
        directories[:] = [d for d in directories if d != '.git'
                          and not (prefix + d + '/').startswith(EXCLUDED_DIRECTORIES)]
        found += [prefix + d for d in directories if (Path(base) / d).is_symlink()]
        found += [prefix + f for f in files if f not in SKIPPED_BASENAMES]
    return found


def required_paths(root):
    tracked = git(root, 'ls-tree', '-r', '--name-only', '-z', 'HEAD', text=True).split('\0')
    paths = REQUIRED | {p for p in tracked + present_paths(root) if in_scope(p)}
    for name in sorted(paths):
        path = root / name
        if not path.is_file() or any(p.is_symlink() for p in [path] + list(path.parents) if p != root and root in p.parents):
            raise ValueError('required input missing or linked: ' + name)
    return paths


def committed_hashes(root, names):
    """Read immutable HEAD blob bytes; index flags cannot suppress this check."""
    names = sorted(names)
    requests = ''.join('HEAD:' + name + '\n' for name in names).encode('utf-8')
    raw = git(root, 'cat-file', '--batch', input=requests)
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
    """Inventory untracked files independently of Git's optional directory walk."""
    tracked = set(git(root, 'ls-tree', '-r', '--name-only', '-z', 'HEAD', text=True).split('\0'))
    present = {name for name in present_paths(root) if in_scope(name)}
    modified = git(root, 'diff', '--name-only', '--no-renames', '-z', 'HEAD', text=True)
    dirty = {name for name in modified.split('\0') if in_scope(name)} | (present - tracked)
    current = hashes(root)
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
        dirty = dirty_inputs(root)
        if dirty:
            p.error('behavior inputs must be clean before manifest generation: ' + ', '.join(dirty))
        values = hashes(root)
        subject_commit = git(root, 'rev-parse', 'HEAD', text=True).strip()
        if not re.fullmatch(r'(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})', subject_commit):
            raise ValueError('git rev-parse HEAD returned invalid commit identity')
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        p.error(str(error))
    result = {'schema': 1, 'kind': 'behavior-inputs', 'subject_commit': subject_commit,
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
