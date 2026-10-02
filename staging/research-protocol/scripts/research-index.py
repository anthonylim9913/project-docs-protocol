#!/usr/bin/env python3
"""Read a bounded research tree without a prerequisite Doctor invocation."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
from research_paths import SafeTree
from research_records import ID_RE, record_id


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('root', type=Path)
    p.add_argument('--topic')
    p.add_argument('--id')
    a = p.parse_args(argv)
    if a.id is not None and not ID_RE.fullmatch(a.id):
        print('REJECT: requested id must be a supported four-digit stable ID', file=sys.stderr)
        return 1
    base = a.root / 'research'
    if not base.exists() and not base.is_symlink():
        print('SKIP research: directory absent')
        return 0
    try:
        with SafeTree(base) as tree:
            records = tree.records()
        if 'INDEX.md' not in records:
            raise ValueError('research-index: INDEX.md missing')
        if a.id is not None:
            hits = [body for name, body in records.items() if name != 'INDEX.md'
                    if record_id(body) == a.id]
            if len(hits) > 1:
                raise ValueError('duplicate id ' + a.id)
            if not hits:
                raise ValueError('id not found: ' + a.id)
            print(hits[0])
        else:
            lines = records['INDEX.md'].splitlines()
            hits = [line for line in lines if not a.topic or a.topic.lower() in line.lower()]
            print('\n'.join(hits))
            if not hits:
                return 1
    except (OSError, ValueError, NotImplementedError) as error:
        print('REJECT: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
