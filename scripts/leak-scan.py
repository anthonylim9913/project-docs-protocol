#!/usr/bin/env python3
"""Scan local Git history using private, external regular expressions.

Exit 0: clean or unconfigured; 1: hits; 2: could not run. Each nonblank,
non-comment patterns-file line is one Python regex, applied per decoded line.
NUL in the first 8,000 bytes marks a binary blob (Git's usual heuristic).
UTF-8 text is decoded with replacement. No network or repository writes.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


class ScanError(Exception):
    pass


def git(*args):
    try:
        result = subprocess.run(['git', *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:
        raise ScanError('could not start git') from None
    if result.returncode:
        # Git errors can echo private input, filenames or remote addresses.
        raise ScanError('git command failed')
    return result.stdout


def configured_patterns(explicit):
    if explicit is not None:
        return explicit
    if os.environ.get('LEAK_SCAN_PATTERNS'):
        return os.environ['LEAK_SCAN_PATTERNS']
    try:
        result = subprocess.run(['git', 'config', '--get', 'leakscan.patterns'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:
        raise ScanError('could not read git configuration') from None
    if result.returncode == 1:
        return None
    if result.returncode:
        raise ScanError('could not read git configuration')
    value = result.stdout.decode('utf-8', 'strict').removesuffix('\n')
    if not value:
        raise ScanError('configured patterns path is empty')
    return value


def read_patterns(filename):
    # Metadata may live outside the working tree (linked worktrees or a
    # separate Git directory); it is still part of the repository. Remove
    # only Git's terminating newline, never whitespace from the path itself.
    boundaries = [Path(os.fsdecode(git('rev-parse', flag)).removesuffix('\n')).resolve()
                  for flag in ('--show-toplevel', '--absolute-git-dir', '--git-common-dir')]
    path = Path(filename).expanduser().resolve()
    for boundary in boundaries:
        try:
            path.relative_to(boundary)
        except ValueError:
            continue
        raise ScanError('patterns file must be outside the repository')
    try:
        lines = path.read_text(encoding='utf-8').splitlines()
    except (OSError, UnicodeError):
        raise ScanError('could not read configured patterns file') from None
    patterns = []
    for number, line in enumerate(lines, 1):
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        try:
            patterns.append((number, re.compile(line)))
        except re.error:
            raise ScanError('invalid regex at pattern line {}'.format(number)) from None
    return patterns


def resolve_commit(revision):
    value = git('rev-parse', '--verify', '--end-of-options', revision + '^{commit}').strip()
    if not re.fullmatch(rb'[0-9a-f]{40}|[0-9a-f]{64}', value):
        raise ScanError('invalid git commit identity')
    return value.decode('ascii')


def commit_list(arguments):
    values = git('rev-list', *arguments, '--').splitlines()
    if any(not re.fullmatch(rb'[0-9a-f]{40}|[0-9a-f]{64}', value) for value in values):
        raise ScanError('invalid git commit list')
    return [value.decode('ascii') for value in values]


def commits_to_scan(range_arg, stream):
    commits = set()
    if range_arg is not None:
        if range_arg.count('..') != 1 or '...' in range_arg:
            raise ScanError('range must be A..B')
        before, after = range_arg.split('..')
        if not before or not after:
            raise ScanError('range must be A..B')
        start, end = resolve_commit(before), resolve_commit(after)
        commits.update(commit_list([end, '^' + start]))
    else:
        for line in stream:
            parts = line.split()
            if len(parts) != 4:
                raise ScanError('malformed pre-push input')
            _, local, _, remote = parts
            if any(not re.fullmatch(r'[0-9a-fA-F]{40}|[0-9a-fA-F]{64}', sha) for sha in (local, remote)):
                raise ScanError('malformed pre-push identity')
            if set(local) == {'0'}:
                continue  # A deletion publishes no commits.
            tip = resolve_commit(local)
            if set(remote) == {'0'}:
                commits.update(commit_list([tip, '--not', '--remotes']))
            else:
                commits.update(commit_list([tip, '^' + resolve_commit(remote)]))
    return sorted(commits)


def scan_lines(commit, location, data, patterns):
    hits = 0
    for number, line in enumerate(data.decode('utf-8', 'replace').splitlines(), 1):
        for pattern_line, pattern in patterns:
            if pattern.search(line):
                print('HIT {} {} line {}; pattern line {}'.format(commit, location, number, pattern_line))
                hits += 1
    return hits


def scan_commit(commit, patterns):
    raw = git('cat-file', 'commit', commit)
    headers, separator, message = raw.partition(b'\n\n')
    if not separator:
        raise ScanError('malformed commit object')
    hits = scan_lines(commit, 'commit message', message, patterns)
    for field, label in ((b'author ', 'author'), (b'committer ', 'committer')):
        identities = [line[len(field):] for line in headers.splitlines() if line.startswith(field)]
        if len(identities) != 1:
            raise ScanError('malformed commit identity')
        match = re.fullmatch(rb'(.*) <([^<>]*)> -?\d+ [+-]\d{4}', identities[0])
        if not match:
            raise ScanError('malformed commit identity')
        for index, kind in ((1, 'name'), (2, 'email')):
            hits += scan_lines(commit, label + ' ' + kind, match[index], patterns)
    # Compare merges against every parent; --no-renames treats a rename as an
    # added blob. --raw provides object IDs, avoiding path/revision ambiguity.
    records = git('-c', 'log.diffMerges=separate', 'diff-tree', '--root', '-m', '-r',
                  '--no-commit-id', '--no-renames', '--no-ext-diff', '--raw', '-z', commit, '--').split(b'\0')
    blobs = set()
    index = 0
    while index < len(records) - 1:
        header = records[index].split()
        if len(header) != 5 or not header[0].startswith(b':'):
            raise ScanError('malformed git tree diff')
        path = records[index + 1]
        index += 2
        if header[4] == b'D' or header[1] == b'160000':
            continue  # Deleted entries and submodule commits are not blobs.
        if not re.fullmatch(rb'[0-9a-f]{40}|[0-9a-f]{64}', header[3]):
            raise ScanError('malformed blob identity')
        blobs.add((header[3], path))
    binary = 0
    for oid, path in sorted(blobs):
        data = git('cat-file', 'blob', oid.decode('ascii'))
        if b'\0' in data[:8000]:
            binary += 1
            continue
        # JSON quoting keeps newline/tab/control characters on a single log line.
        location = 'path ' + json.dumps(os.fsdecode(path), ensure_ascii=True)
        hits += scan_lines(commit, location, data, patterns)
    return hits, binary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--patterns', metavar='PATH', help='private regex file outside repository')
    parser.add_argument('--range', metavar='A..B', help='otherwise read pre-push ref updates on stdin')
    args = parser.parse_args(argv)
    try:
        filename = configured_patterns(args.patterns)
        if filename is None:
            print('leak-scan: not configured; no scan performed')
            return 0
        patterns = read_patterns(filename)
        commits = commits_to_scan(args.range, sys.stdin)
        hits = binary = 0
        for commit in commits:
            found, skipped = scan_commit(commit, patterns)
            hits += found
            binary += skipped
        print('{} leak-scan: {} commits; {} hits; binary skipped {}'.format(
            'HITS' if hits else 'CLEAN', len(commits), hits, binary))
        return 1 if hits else 0
    except (ScanError, OSError, UnicodeError, ValueError, RuntimeError):
        # Never print arbitrary exception text: it may contain a private path,
        # regex or Git-provided text. ScanError messages above are safe literals.
        error = sys.exc_info()[1]
        detail = str(error) if isinstance(error, ScanError) else 'could not run'
        print('ERROR leak-scan: ' + detail, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
