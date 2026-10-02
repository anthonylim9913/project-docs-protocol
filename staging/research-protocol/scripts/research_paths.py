"""Descriptor-anchored research paths shared by all three public helpers.

The selected project parent is trusted. Every component from research/ down is
opened without following links. Noncooperating hostile renames cannot be made a
single filesystem-wide transaction; callers revalidate before each effect.
"""
from contextlib import contextmanager
import os
from pathlib import Path, PurePosixPath
import re
import stat


class UnsafePath(ValueError):
    pass


def reserved_sidecar(name):
    """Helper metadata is reserved over the entire accepted filename."""
    return re.fullmatch(r'\..+\.(?:lock|tmp(?:\..+)?)', name, re.DOTALL) is not None


def capabilities():
    if (not hasattr(os, 'O_NOFOLLOW') or not hasattr(os, 'O_DIRECTORY') or
            not hasattr(os, 'O_NONBLOCK') or os.open not in os.supports_dir_fd or
            os.stat not in os.supports_dir_fd):
        raise UnsafePath('secure descriptor operations unavailable')


def parts(name):
    raw = str(name)
    if (not raw or raw.startswith('/') or '\\' in raw or '\x00' in raw or
            any(p in ('', '.', '..') for p in raw.split('/'))):
        raise UnsafePath('path escape or invalid research path')
    return PurePosixPath(raw).parts


def identity(info):
    return info.st_dev, info.st_ino


def check_type(info, label, directory=False):
    if stat.S_ISLNK(info.st_mode):
        raise UnsafePath('symlinked research path: ' + label)
    if directory:
        if not stat.S_ISDIR(info.st_mode):
            raise UnsafePath('research path is not a directory: ' + label)
    else:
        if not stat.S_ISREG(info.st_mode):
            raise UnsafePath('research path must be a regular file: ' + label)
        if info.st_nlink != 1:
            raise UnsafePath('hard-linked research file: ' + label)


def validate(fd, parent, name, directory=False):
    actual = os.fstat(fd)
    visible = os.stat(name, dir_fd=parent, follow_symlinks=False)
    if identity(actual) != identity(visible):
        raise UnsafePath('research path identity changed: ' + name)
    check_type(actual, name, directory)
    check_type(visible, name, directory)
    return actual


def open_checked(parent, name, flags=os.O_RDONLY, directory=False, create=False):
    try:
        before = os.stat(name, dir_fd=parent, follow_symlinks=False)
        check_type(before, name, directory)
    except FileNotFoundError:
        if not create:
            raise
        before = None
    flags |= os.O_NOFOLLOW | os.O_NONBLOCK
    if directory:
        flags |= os.O_DIRECTORY
    if create:
        flags |= os.O_CREAT
    fd = os.open(name, flags, 0o600, dir_fd=parent)
    try:
        after = validate(fd, parent, name, directory)
        if before is not None and identity(before) != identity(after):
            raise UnsafePath('research path identity changed: ' + name)
        return fd
    except BaseException:
        os.close(fd)
        raise


def read_fd(fd):
    os.lseek(fd, 0, os.SEEK_SET)
    blocks = []
    while True:
        block = os.read(fd, 65536)
        if not block:
            return b''.join(blocks)
        blocks.append(block)


class SafeTree:
    def __init__(self, base):
        capabilities()
        base = Path(base)
        if '..' in base.parts:
            raise UnsafePath('path escape in research root')
        self.base = base.parent.resolve() / base.name
        self.parent = os.open(str(self.base.parent), os.O_RDONLY | os.O_DIRECTORY)
        try:
            self.fd = open_checked(self.parent, self.base.name, directory=True)
        except BaseException:
            os.close(self.parent)
            raise

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        os.close(self.fd)
        os.close(self.parent)

    def validate_root(self):
        # Reopen the visible parent: the held parent descriptor alone cannot
        # detect a rename of the project itself.
        parent = os.open(str(self.base.parent), os.O_RDONLY | os.O_DIRECTORY)
        try:
            if identity(os.fstat(parent)) != identity(os.fstat(self.parent)):
                raise UnsafePath('research parent identity changed')
            validate(self.fd, self.parent, self.base.name, True)
        finally:
            os.close(parent)

    @contextmanager
    def directory(self, components):
        chain = []
        fd = self.fd
        try:
            for name in components:
                child = open_checked(fd, name, directory=True)
                chain.append((child, fd, name))
                fd = child
            def revalidate():
                self.validate_root()
                for child, parent, name in chain:
                    validate(child, parent, name, True)
            revalidate()
            yield fd, revalidate
        finally:
            for child, _, _ in reversed(chain):
                os.close(child)

    def read(self, name):
        components = parts(name)
        with self.directory(components[:-1]) as (parent, revalidate):
            fd = open_checked(parent, components[-1])
            try:
                revalidate()
                validate(fd, parent, components[-1])
                data = read_fd(fd)
                validate(fd, parent, components[-1])
                revalidate()
                return data
            finally:
                os.close(fd)

    def records(self):
        names = []
        def walk(prefix):
            with self.directory(prefix) as (fd, revalidate):
                for name in sorted(os.listdir(fd)):
                    parts(name)
                    info = os.stat(name, dir_fd=fd, follow_symlinks=False)
                    if stat.S_ISDIR(info.st_mode):
                        walk(prefix + (name,))
                    else:
                        check_type(info, name)
                        if name.endswith('.md') and not reserved_sidecar(name):
                            names.append('/'.join(prefix + (name,)))
                revalidate()
        walk(())
        return {name: self.read(name).decode('utf-8') for name in names}
