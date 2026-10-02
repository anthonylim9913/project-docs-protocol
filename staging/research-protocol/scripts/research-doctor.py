#!/usr/bin/env python3
"""Read-only structural checks; provenance shape is not source authentication."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import re
import stat
from research_paths import SafeTree, open_checked, parts
from research_records import ID_RE, heading_tokens, record_id

TOKEN_RE = re.compile(r'\b(?:SRC|NOTE|RQ|SYN)-[A-Za-z0-9_-]+\b')
REF_RE = re.compile(r'\b(?:SRC|NOTE|RQ|SYN)-[0-9]{4}\b')
# Companion signature: an INDEX.md naming stable IDs (malformed digit runs
# included, so they still fail), or a canonically named record.
INDEX_ID_RE = re.compile(r'\b(?:SRC|NOTE|RQ|SYN)-[0-9]+')
RECORD_FOLDERS = {'sources': 'SRC', 'notes': 'NOTE', 'questions': 'RQ', 'synthesis': 'SYN'}


def fields(body, ident, errors):
    result = {}
    for line in body.splitlines():
        match = re.fullmatch(r'[-*]?[ \t]*([A-Za-z][A-Za-z0-9 -]*?)[ \t]*:[ \t]*(.*)', line)
        if match:
            name, value = match.groups()
            name = name.lower()
            if name in result:
                errors.append(ident + ' duplicate field ' + name)
            result[name] = value.strip()
    return result


def needed(values, name, ident, errors):
    if not values.get(name.lower(), '').strip():
        errors.append(ident + ' missing nonempty ' + name)


def provenance(values, ident, errors):
    if 'status' in values and 'lifecycle' in values:
        errors.append(ident + ' duplicate lifecycle field (Status and Lifecycle)')
    accessibility = values.get('accessibility', 'public')
    if accessibility not in ('public', 'private', 'unavailable'):
        errors.append(ident + ' unknown Accessibility')
    if not values.get('status') and not values.get('lifecycle'):
        errors.append(ident + ' missing nonempty Status or Lifecycle')
    if 'content-sha256' in values and not re.fullmatch(r'[0-9a-fA-F]{64}', values['content-sha256']):
        errors.append(ident + ' has invalid Content-SHA256')
    required = {'public': ('URL', 'Accessed', 'Passage'),
                'private': ('Private-Reference', 'Limitation'),
                'unavailable': ('URL', 'Attempted-Access', 'Limitation')}
    for name in required.get(accessibility, ()):
        needed(values, name, ident, errors)
    if accessibility == 'public' and not values.get('version') and not values.get('content-sha256'):
        errors.append(ident + ' missing nonempty Version or Content-SHA256')


def inspect(records):
    errors = []
    if 'INDEX.md' not in records:
        return ['research-index: INDEX.md missing'], {}
    index_text = records['INDEX.md']
    texts = {name: body for name, body in records.items() if name != 'INDEX.md'}
    ids = {}
    declared = {}
    for path, body in texts.items():
        for heading_id in heading_tokens(body):
            if re.match(r'^(?:SRC|NOTE|RQ|SYN)-', heading_id) and not ID_RE.fullmatch(heading_id):
                errors.append('malformed id ' + heading_id + ' (four digits required)')
        for near in TOKEN_RE.findall(body):
            if not ID_RE.fullmatch(near):
                errors.append('malformed id ' + near + ' (four digits required)')
        try:
            ident = record_id(body)
        except ValueError as error:
            errors.append(path + ': ' + str(error))
            continue
        declared[path] = ident
        if ident is not None:
            if ident in ids:
                errors.append('duplicate id ' + ident)
            else:
                ids[ident] = path
            values = fields(body, ident, errors)
            if ident.startswith('SRC-'):
                provenance(values, ident, errors)
            if ident.startswith('NOTE-'):
                needed(values, 'Source', ident, errors)
            if ident.startswith('RQ-'):
                needed(values, 'Evidence', ident, errors)
            if ident.startswith('SYN-'):
                needed(values, 'Claim', ident, errors)
                if not any(values.get(k) for k in ('decision', 'owner decision', 'recommendation')):
                    errors.append(ident + ' missing nonempty Decision')
    for token in TOKEN_RE.findall(index_text):
        if not ID_RE.fullmatch(token):
            errors.append('malformed id ' + token + ' in INDEX.md (four digits required)')
    index_refs = set(REF_RE.findall(index_text))
    all_refs = set(REF_RE.findall(index_text + '\n' + '\n'.join(texts.values())))
    missing = sorted(all_refs - set(ids))
    if missing:
        errors.append('missing references ' + ', '.join(missing))
    if not index_refs:
        errors.append('INDEX.md has no stable IDs')
    for ident, path in ids.items():
        candidate_lines = [line for line in index_text.splitlines() if re.search(r'\b' + re.escape(ident) + r'\b', line)]
        valid_link = False
        for line in candidate_lines:
            links = re.findall(r'`([^`]+\.md)`', line) + re.findall(r'\(([^)]*\.md)\)', line)
            for link in links:
                try:
                    parts(link)
                except ValueError:
                    errors.append('unsafe INDEX.md link: ' + link)
                    continue
                if declared.get(link) == ident:
                    valid_link = True
        if not candidate_lines:
            errors.append(ident + ' absent from INDEX.md')
        elif not valid_link:
            errors.append(ident + ' has unresolved INDEX.md link')
        values = fields(texts[path], ident, [])
        for name in ('status', 'lifecycle', 'correction', 'superseded', 'superseded-by'):
            if name not in values:
                continue
            value = values[name]
            relation = re.match(r'^(?:superseded by|correction of|retracted by)(?:[ \t]+|$)', value)
            if relation:
                target = value[relation.end():].split()[0] if value[relation.end():].strip() else ''
            elif name not in ('status', 'lifecycle'):
                target = value
            else:
                continue
            if not ID_RE.fullmatch(target) or target == ident or target not in ids:
                errors.append(ident + ' has invalid supersession target ' + (target or '(empty)'))
    return errors, ids


def not_companion(base):
    """Return why research/ is not a research-protocol folder, or None if it is.

    Only research/INDEX.md and the four canonical record folders are probed,
    one level deep and without following links, so an unrelated folder (for
    example one holding a virtualenv) is never walked.
    """
    with SafeTree(base) as tree:
        names = set(os.listdir(tree.fd))
        reason = 'no INDEX.md'
        if 'INDEX.md' in names:
            try:
                text = tree.read('INDEX.md').decode('utf-8', 'replace')
            except (OSError, ValueError):
                return None  # an unsafe INDEX.md is reported by the full checks
            if INDEX_ID_RE.search(text):
                return None
            reason = 'INDEX.md has no stable IDs'
        for folder, prefix in RECORD_FOLDERS.items():
            if folder not in names:
                continue
            info = os.stat(folder, dir_fd=tree.fd, follow_symlinks=False)
            if not stat.S_ISDIR(info.st_mode):
                continue
            fd = open_checked(tree.fd, folder, directory=True)
            try:
                if any(re.fullmatch(prefix + r'-[0-9]{4}\.md', name) for name in os.listdir(fd)):
                    return None
            finally:
                os.close(fd)
        return reason


def main(argv=None):
    p = argparse.ArgumentParser(description=(
        'Read-only structural checks for the optional research-protocol companion in <root>/research/. '
        'Absence is valid (SKIP, exit 0): no research/ folder, or a research/ folder without the '
        'companion signature (research/INDEX.md naming stable IDs, or a canonical record such as '
        'sources/SRC-0001.md). Exit 1 on any FAIL.'))
    p.add_argument('root', type=Path, help='project root to judge; only its research/ folder is inspected')
    args = p.parse_args(argv)
    base = args.root / 'research'
    if not base.exists() and not base.is_symlink():
        print('SKIP research: directory absent')
        return 0
    try:
        # A linked research/ is refused below without being followed.
        if base.is_dir() and not base.is_symlink():
            reason = not_companion(base)
            if reason is not None:
                print('SKIP research: research/ present but not a research-protocol folder (' + reason + ')')
                return 0
        with SafeTree(base) as tree:
            records = tree.records()
        errors, ids = inspect(records)
    except (OSError, ValueError, NotImplementedError) as error:
        errors, ids = [str(error)], {}
    if errors:
        for error in errors:
            print('FAIL', error)
        return 1
    print('PASS research-index: %d records; provenance fields and references are structurally consistent' % len(ids))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
