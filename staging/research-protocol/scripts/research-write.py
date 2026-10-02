#!/usr/bin/env python3
"""Replace one existing research record using a stable cooperative lock."""
from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path
import re
import stat
import sys
import uuid
try:
    import fcntl
except ImportError:
    fcntl = None
from research_paths import SafeTree, UnsafePath, check_type, identity, open_checked, parts, read_fd, reserved_sidecar, validate


def research_target(root, path):
    """Return the selected project's research/ directory and the target below it.

    The caller-selected project root is trusted, so links above or at the root
    are accepted. The target must continue from that root with research/ and at
    least one more component. Every component from research/ down is later
    opened without following links, so a linked research/ or subdirectory is
    refused before anything is created.
    """
    if '..' in path.parts:
        raise UnsafePath('path escape in research target')
    root = Path.cwd() if root is None else Path(root)
    try:
        project = root.resolve(strict=True)
    except (OSError, RuntimeError):
        raise UnsafePath('project root not found: ' + str(root)) from None
    if not project.is_dir():
        raise UnsafePath('project root is not a directory: ' + str(root))
    path = Path.cwd() / path
    below = ()
    for depth in range(1, len(path.parts) + 1):
        # The shallowest spelling of the project root wins, so a link inside
        # research/ that points back at the root cannot shorten the path.
        try:
            spelling = Path(*path.parts[:depth]).resolve()
        except RuntimeError:  # link loop on older Pythons: not the project root
            continue
        if spelling == project:
            below = path.parts[depth:]
            break
    if below[:1] != ('research',) or len(below) < 2:
        raise UnsafePath('target must be inside research/ of the project root ' + str(project)
                         + '; select the project with --root')
    # below[0] is 'research' here; the check above is what confines the write.
    return project / below[0], parts('/'.join(below[1:]))


def write_record(path, content, expected, root=None):
    if fcntl is None:
        raise UnsafePath('cooperative locking unavailable; write refused')
    if not re.fullmatch(r'[0-9a-f]{64}', expected):
        raise UnsafePath('expected SHA256 must be 64 lowercase hex digits')
    base, components = research_target(root, path)
    name = components[-1]
    if reserved_sidecar(name):
        raise UnsafePath('reserved helper sidecar cannot be a write target')
    lock_name = '.' + name + '.lock'
    with SafeTree(base) as tree, tree.directory(components[:-1]) as (parent, revalidate):
        # Reject unsafe historical sidecars; they are never reused or removed.
        legacy = '.' + name + '.tmp'
        try:
            check_type(os.stat(legacy, dir_fd=parent, follow_symlinks=False), legacy)
        except FileNotFoundError:
            pass
        probe = open_checked(parent, name)
        os.close(probe)
        lock = open_checked(parent, lock_name, os.O_RDWR, create=True)
        target = temp = None
        temp_name = None
        try:
            fcntl.flock(lock, fcntl.LOCK_EX)
            revalidate()
            validate(lock, parent, lock_name)
            target = open_checked(parent, name)
            original = validate(target, parent, name)
            actual = hashlib.sha256(read_fd(target)).hexdigest()
            if actual != expected:
                raise UnsafePath('stale target hash ' + actual)
            temp_name = '.' + name + '.tmp.' + uuid.uuid4().hex
            temp = os.open(temp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                           0o600, dir_fd=parent)
            with os.fdopen(os.dup(temp), 'wb') as stream:
                stream.write(content.encode('utf-8'))
                stream.flush()
                # Writing may clear set-ID bits. Apply and verify the complete
                # original permission mask only after all content is flushed.
                os.fchmod(temp, stat.S_IMODE(original.st_mode))
                if stat.S_IMODE(os.fstat(temp).st_mode) != stat.S_IMODE(original.st_mode):
                    raise UnsafePath('target permission bits could not be preserved')
                os.fsync(stream.fileno())
            revalidate()
            validate(lock, parent, lock_name)
            validate(temp, parent, temp_name)
            validate(target, parent, name)
            if hashlib.sha256(read_fd(target)).hexdigest() != expected:
                raise UnsafePath('stale target hash before replacement')
            os.replace(temp_name, name, src_dir_fd=parent, dst_dir_fd=parent)
            os.fsync(parent)
        finally:
            # Never unlink the stable lock: waiters must share its inode.
            try:
                if temp is not None:
                    try:
                        visible = os.stat(temp_name, dir_fd=parent, follow_symlinks=False)
                        if identity(visible) == identity(os.fstat(temp)):
                            os.unlink(temp_name, dir_fd=parent)
                    except FileNotFoundError:
                        pass
                    finally:
                        os.close(temp)
            finally:
                try:
                    if target is not None:
                        os.close(target)
                finally:
                    os.close(lock)


def main(argv=None):
    p = argparse.ArgumentParser(description='Replace one existing record inside <root>/research/. '
                                'Targets anywhere else, or reached through a link at or below research/, are refused.')
    p.add_argument('path', type=Path, help='existing record under <root>/research/; a relative path is taken from the current directory')
    p.add_argument('content')
    p.add_argument('--expected-sha256', required=True)
    p.add_argument('--root', type=Path, default=None,
                   help='project root whose research/ folder may be written (default: the current directory)')
    a = p.parse_args(argv)
    try:
        write_record(a.path, a.content, a.expected_sha256, a.root)
    except (OSError, ValueError, NotImplementedError) as error:
        print('REJECT: ' + str(error), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('REJECT: interrupted research write', file=sys.stderr)
        return 1
    print('WROTE ' + str(a.path))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
