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
        result = subprocess.run(['git', '--no-replace-objects', *args],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env=dict(os.environ, GIT_NO_LAZY_FETCH='1'))
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
        result = subprocess.run(['git', '--no-replace-objects', 'config', '--get', 'leakscan.patterns'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env=dict(os.environ, GIT_NO_LAZY_FETCH='1'))
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
        # Lexical containment alone misses alternate casing on a filesystem
        # that preserves case but compares names without it.
        for ancestor in (path, *path.parents):
            try:
                if os.path.samefile(ancestor, boundary):
                    raise ScanError('patterns file must be outside the repository')
            except FileNotFoundError:
                continue
        try:
            path.relative_to(boundary)
        except ValueError:
            continue
        raise ScanError('patterns file must be outside the repository')
    for tracked in git('-C', str(boundaries[0]), 'ls-files', '-z').split(b'\0'):
        if not tracked:
            continue
        try:
            if os.path.samefile(path, boundaries[0] / os.fsdecode(tracked)):
                raise ScanError('patterns file must be outside the repository')
        except FileNotFoundError:
            continue
    try:
        lines = path.read_text(encoding='utf-8-sig').splitlines()
    except (OSError, UnicodeError):
        raise ScanError('could not read configured patterns file') from None
    patterns = []
    for number, line in enumerate(lines, 1):
        line = line.rstrip()
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        try:
            patterns.append((number, re.compile(line)))
        except Exception:
            raise ScanError('invalid regex at pattern line {}'.format(number)) from None
    if not patterns:
        raise ScanError('patterns file has no active patterns')
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


def pushed_object(revision):
    oid = git('rev-parse', '--verify', '--end-of-options', revision + '^{object}').strip()
    tags = set()
    while True:
        if not re.fullmatch(rb'[0-9a-f]{40}|[0-9a-f]{64}', oid):
            raise ScanError('invalid git object identity')
        value = oid.decode('ascii')
        kind = git('cat-file', '-t', value).strip()
        if kind != b'tag':
            return (value if kind == b'commit' else None), tags
        if value in tags:
            raise ScanError('invalid tag chain')
        tags.add(value)
        raw = git('cat-file', 'tag', value)
        first = raw.split(b'\n', 1)[0]
        if not first.startswith(b'object '):
            raise ScanError('malformed tag object')
        oid = first[len(b'object '):]


def commits_to_scan(range_arg, stream, remote_name=None):
    commits, refs, tags = set(), set(), set()
    if range_arg is not None:
        if '..' not in range_arg:
            commits.update(commit_list([resolve_commit(range_arg)]))
        else:
            if range_arg.count('..') != 1 or '...' in range_arg:
                raise ScanError('range must be TIP or A..B')
            before, after = range_arg.split('..')
            if not before or not after:
                raise ScanError('range must be TIP or A..B')
            start, end = resolve_commit(before), resolve_commit(after)
            commits.update(commit_list([end, '^' + start]))
    else:
        saw_line = False
        for line in stream:
            saw_line = True
            parts = line.split()
            if len(parts) != 4:
                raise ScanError('malformed pre-push input')
            local_ref, local, remote_ref, remote = parts
            if any(not re.fullmatch(r'[0-9a-fA-F]{40}|[0-9a-fA-F]{64}', sha) for sha in (local, remote)):
                raise ScanError('malformed pre-push identity')
            if set(local) == {'0'}:
                continue  # Deletions publish no objects or new ref names.
            refs.update((local_ref, remote_ref))
            tip, pushed_tags = pushed_object(local)
            tags.update(pushed_tags)
            if tip is None:
                continue
            if set(remote) == {'0'}:
                arguments = [tip]
                if remote_name:
                    arguments += ['--not', '--remotes=' + remote_name]
                commits.update(commit_list(arguments))
            else:
                previous, _ = pushed_object(remote)
                commits.update(commit_list([tip] + (['^' + previous] if previous else [])))
        if not saw_line:
            raise ScanError('nothing to scan')
    return sorted(commits), sorted(refs), sorted(tags)


def scan_lines(commit, location, data, patterns):
    hits = 0
    for number, line in enumerate(data.decode('utf-8', 'replace').splitlines(), 1):
        for pattern_line, pattern in patterns:
            if pattern.search(line):
                print('HIT {} {} line {}; pattern line {}'.format(commit, location, number, pattern_line))
                hits += 1
    return hits


def scan_tag(oid, patterns):
    raw = git('cat-file', 'tag', oid)
    headers, separator, message = raw.partition(b'\n\n')
    if not separator:
        raise ScanError('malformed tag object')
    hits = scan_lines(oid, 'tag message', message, patterns)
    taggers = [line[len(b'tagger '):] for line in headers.splitlines()
               if line.startswith(b'tagger ')]
    if len(taggers) != 1:
        raise ScanError('malformed tag identity')
    match = re.fullmatch(rb'(.*) <([^<>]*)> -?\d+ [+-]\d{4}', taggers[0])
    if not match:
        raise ScanError('malformed tag identity')
    for index, kind in ((1, 'name'), (2, 'email')):
        hits += scan_lines(oid, 'tag tagger ' + kind, match[index], patterns)
    return hits


def path_location(path, patterns):
    text = path.decode('utf-8', 'replace')
    if any(pattern.search(line) for _, pattern in patterns
           for line in [text, *text.splitlines()]):
        return 'path [redacted]'
    # Quote newlines, tabs and controls to keep diagnostics on one line.
    return 'path ' + json.dumps(os.fsdecode(path), ensure_ascii=True)


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
    blobs, paths = set(), set()
    index = 0
    while index < len(records) - 1:
        header = records[index].split()
        if len(header) != 5 or not header[0].startswith(b':'):
            raise ScanError('malformed git tree diff')
        path = records[index + 1]
        index += 2
        paths.add(path)
        if header[4] == b'D' or header[1] == b'160000':
            continue  # Deleted entries and submodule commits are not blobs.
        if not re.fullmatch(rb'[0-9a-f]{40}|[0-9a-f]{64}', header[3]):
            raise ScanError('malformed blob identity')
        blobs.add((header[3], path))
    for path in sorted(paths):
        hits += scan_lines(commit, 'changed path', path, patterns)
    binary = 0
    for oid, path in sorted(blobs):
        data = git('cat-file', 'blob', oid.decode('ascii'))
        if b'\0' in data[:8000]:
            binary += 1
            continue
        location = path_location(path, patterns)
        hits += scan_lines(commit, location, data, patterns)
    return hits, binary


class PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ScanError('invalid arguments')


def scan_main(argv):
    parser = PrivateArgumentParser(description=__doc__)
    parser.add_argument('--patterns', metavar='PATH', help='private regex file outside repository')
    parser.add_argument('--range', metavar='TIP|A..B', help='otherwise read pre-push ref updates on stdin')
    parser.add_argument('remote_name', nargs='?', help='destination remote name supplied by Git')
    parser.add_argument('remote_url', nargs='?', help='destination URL supplied by Git (unused)')
    args = parser.parse_args(argv)
    filename = configured_patterns(args.patterns)
    if filename is None:
        print('leak-scan: not configured; no scan performed')
        return 0
    patterns = read_patterns(filename)
    commits, refs, tags = commits_to_scan(args.range, sys.stdin, args.remote_name)
    hits = binary = 0
    for ref in refs:
        hits += scan_lines('ref', 'ref name', ref.encode('utf-8'), patterns)
    for tag in tags:
        hits += scan_tag(tag, patterns)
    for commit in commits:
        found, skipped = scan_commit(commit, patterns)
        hits += found
        binary += skipped
    print('{} leak-scan: {} commits; {} hits; binary skipped {}'.format(
        'HITS' if hits else 'CLEAN', len(commits), hits, binary))
    return 1 if hits else 0


def main(argv=None):
    try:
        return scan_main(argv)
    except ScanError as error:
        # Only locally authored fixed messages may be printed.
        print('ERROR leak-scan: ' + str(error), file=sys.stderr)
        return 2
    except Exception:
        # Includes resource errors and unexpected library failures. Never echo
        # exception text, a traceback, arguments, paths or private patterns.
        print('ERROR leak-scan: could not run', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
