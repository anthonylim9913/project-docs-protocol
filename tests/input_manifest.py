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

# Binding rule (D-0025): every file in the repository, tracked at HEAD or present on disk,
# is a behavior input unless it is listed here. The list is the reviewed exception, not
# an inclusion allowlist: a file added later is bound by default.
EXCLUDED = frozenset({
    # Live registers: rewritten by every Close, state rather than normative input.
    'docs/STATUS.md', 'docs/CHANGELOG.md', 'docs/DECISIONS.md', 'docs/LEDGER.md',
    'docs/LEDGER-ARCHIVE.md',
    # Review reports: dated history of how the repository was checked, not instructions.
    'docs/HARDENING-REVIEW.md', 'docs/LESSONS-REVIEW.md',
})
# Never inputs: version control internals and per-run scratch space.
EXCLUDED_DIRECTORIES = ('.git/', 'tests/.tmp/')
# Finder metadata, skipped by basename only: Python cannot import it, and macOS writes it
# into any folder opened in Finder. Other ignored files stay in scope (an ignored .py runs).
SKIPPED_BASENAMES = frozenset({'.DS_Store'})
# Python executes these, so they are never out of scope: present or committed, they are refused.
BYTECODE_SUFFIXES = ('.pyc', '.pyo', '.so', '.pyd', '.pth')
ROOT_FILES = {'SKILL.md', 'AGENTS.md', 'CLAUDE.md', 'README.md', 'LICENSE'}
DOC_INPUTS = {'docs/README.md', 'docs/MIGRATION.md', 'docs/PROTOCOLS.md', 'docs/SKILL-REGISTRY.md',
              'docs/BRIEF-EXAMPLE.md', 'docs/EVIDENCE.md'}
# Everything the verdict reads from the judging checkout: the code, the frozen cases and
# contract, and the fixtures and template the expectations are computed from (D-0025). A test
# audits the files the runner and validator open against this set. HARNESS_RECORD lists each
# with its SHA-256 in `sha256sum` format; it is bound like any other input but not listed in itself.
HARNESS_FILES = ('tests/validate_acceptance.py', 'tests/acceptance_gate.py', 'tests/acceptance_evidence.py',
                 'tests/input_manifest.py', 'tests/run_acceptance.py',
                 'tests/fixtures/hardening-2026-09-12/acceptance-cases.json') + tuple(
    'tests/fixtures/hardening-2026-09-12/cases/' + n + '.md' for n in (
        'doctor-a1', 'doctor-a1-positive', 'doctor-a2', 'doctor-a2-positive',
        'migration-split-cdata', 'migration-split-pi')) + (
    'tests/fixtures/acceptance-v2/contract.json', 'tests/fixtures/acceptance-v2/contiguous-cdata.md',
    'tests/fixtures/acceptance-v2/contiguous-pi.md', 'tests/fixtures/migration-20/STATUS.md',
    'templates/LEDGER.md')
HARNESS_RECORD = 'tests/harness.sha256'
# Floor, not scope: these must exist even if the rule above were to miss them.
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


# The candidate controls its own .git: config, hooks and replacement refs. Every Git command
# the judge runs goes through git() so none of them can run the candidate's code or show
# content other than the objects' real bytes (D-0027).
GIT_HARDENING = ('-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null')


def git(root, *args, **kwargs):
    """subprocess.check_output for `git -C root ARGS`, hardened against the candidate's .git."""
    env = dict(os.environ, GIT_NO_REPLACE_OBJECTS='1')
    return subprocess.check_output(('git',) + GIT_HARDENING + ('-C', str(root)) + args, env=env, **kwargs)


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
    for base, directories, files in os.walk(root):
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
    """NUL-separated paths include both sides of renames and untracked files."""
    modified = git(root, 'diff', '--name-only', '--no-renames', '-z', 'HEAD', text=True)
    untracked = git(root, 'ls-files', '--others', '-z', text=True)
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


def harness_record(root):
    """The text of HARNESS_RECORD for `root`: `sha256sum` lines, sorted by path.

    validate_acceptance.py checks it (it does not import this module to do so); a reviewer
    checks it with `sha256sum -c tests/harness.sha256` and pins `sha256sum tests/harness.sha256`.
    """
    return ''.join(hashlib.sha256((root / name).read_bytes()).hexdigest() + '  ' + name + '\n'
                   for name in sorted(HARNESS_FILES))


def harness_digest(root):
    """SHA-256 of the record `root` should carry: the value a reviewer pins."""
    return hashlib.sha256(harness_record(root).encode('utf-8')).hexdigest()


def main():
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path); p.add_argument('--out', type=Path)
    p.add_argument('--print-harness-digest', action='store_true',
                   help='print the SHA-256 of the harness record this tree should carry, and exit')
    p.add_argument('--print-harness-record', action='store_true',
                   help='print the harness record (sha256sum format) for this tree, and exit')
    a = p.parse_args(); root = a.root.resolve()
    if a.print_harness_digest:
        print(harness_digest(root))
        return
    if a.print_harness_record:
        print(harness_record(root), end='')
        return
    if a.out is None:
        p.error('--out is required')
    if root == a.out.resolve() or root in a.out.resolve().parents:
        p.error('input manifest output must be outside the reviewed tree')
    try:
        if a.out.exists() or a.out.is_symlink():
            metadata = a.out.lstat()
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                p.error('output must be a regular unlinked file')
        dirty = dirty_inputs(root)
        if dirty:
            shown = ', '.join(dirty[:10]) + (' and %d more' % (len(dirty) - 10) if len(dirty) > 10 else '')
            p.error('behavior inputs must be clean before manifest generation: ' + shown)
        values = hashes(root)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        p.error(str(error))
    result = {'schema': 1, 'kind': 'behavior-inputs', 'subject_commit': git(root, 'rev-parse', 'HEAD', text=True).strip(),
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
