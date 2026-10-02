"""Shared register selection; filesystem discovery is not proof of installation."""
from pathlib import Path

REGISTER = ("STATUS.md", "CHANGELOG.md", "DECISIONS.md")


def has_register(directory):
    return all((Path(directory) / name).is_file() for name in REGISTER)


def select_register(project, explicit=None, pre_install=False):
    """Select a unique complete register, or an explicitly named target.

    Relative explicit paths are relative to the project. Pre-install migration
    can select a two-file source only with both explicit and pre_install set.
    """
    project = Path(project).absolute()
    if not project.is_dir():
        raise ValueError(f"not a directory: {project}")
    if pre_install and explicit is None:
        raise ValueError("--pre-install requires --register-dir; choose the source explicitly")
    if explicit is not None:
        candidate = Path(explicit)
        if not candidate.is_absolute():
            candidate = project / candidate
        names = REGISTER[:2] if pre_install else REGISTER
        if not all((candidate / name).is_file() for name in names):
            raise ValueError("selected register requires " + " + ".join(names))
        return candidate.resolve()
    candidates = []
    for candidate in (project / "docs", project):
        if has_register(candidate) and candidate.resolve() not in candidates:
            candidates.append(candidate.resolve())
    if len(candidates) > 1:
        raise ValueError("two complete registers; choose the owner with --register-dir . or --register-dir docs")
    if not candidates:
        raise ValueError("no complete register (STATUS.md + CHANGELOG.md + DECISIONS.md); "
                         "migration of a pre-install source requires --pre-install --register-dir PATH")
    return candidates[0]
