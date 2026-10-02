#!/usr/bin/env python3
"""Validate the optional project's canonical, versioned skill registry."""
from __future__ import annotations
import argparse, hashlib, re
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
VERSION_RE = re.compile(r"^v?[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")
CONTENT_ID_RE = re.compile(r"sha256:[0-9a-f]{64}")
STATUSES = {"active", "staged", "retired"}
REQUIRED = {"required", "optional"}
HEADER = ("name", "trigger", "lifecycle", "workflow stages", "inputs", "outputs/evidence", "reviewer/gate", "required", "location", "version", "content-id", "missing-capability")

def _registry_path(root: Path, requested: str | None, register_dir: str | None = None) -> Path | None:
    if requested:
        path = Path(requested); return path if path.is_absolute() else root / path
    if register_dir is not None:
        # Same convention as docs-doctor: relative to the project root, or absolute.
        directory = Path(register_dir); directory = directory if directory.is_absolute() else root / directory
        if not directory.is_dir(): raise ValueError(f"register directory not found: {register_dir}")
        path = directory / "SKILL-REGISTRY.md"
        return path if path.is_file() else None
    candidates = [root / "docs" / "SKILL-REGISTRY.md", root / "SKILL-REGISTRY.md"]
    present = [path for path in candidates if path.is_file()]
    if len(present) > 1: raise ValueError("multiple SKILL-REGISTRY.md files; pass --registry or --register-dir")
    return present[0] if present else None

def _rows(text: str):
    errors=[]; rows=[]; in_fence=False; header_at=None
    for number,line in enumerate(text.splitlines(),1):
        if line.strip().startswith("```"): in_fence=not in_fence; continue
        if in_fence or not line.lstrip().startswith("|"): continue
        cells=[c.strip().strip("`") for c in line.strip().strip("|").split("|")]
        if tuple(c.lower() for c in cells)==HEADER: header_at=number; continue
        if header_at is None or all(set(c) <= {"-",":"," "} for c in cells): continue
        if len(cells)!=len(HEADER): errors.append(f"line {number}: expected {len(HEADER)} columns")
        else: rows.append((number,cells))
    if header_at is None: errors.append("missing canonical registry header")
    return rows,errors

def _tree_digest(path: Path) -> str:
    digest=hashlib.sha256()
    for child in sorted(path.rglob("*")):
        rel=child.relative_to(path)
        if child.is_symlink(): raise ValueError(f"symlinked registry target: {rel}")
        if child.is_file() and "__pycache__" not in rel.parts:
            digest.update(str(rel).encode()); digest.update(b"\0"); digest.update(child.read_bytes()); digest.update(b"\0")
    return digest.hexdigest()

def validate(path: Path, project_root: Path | None = None) -> list[str]:
    if path.is_symlink(): return ["registry must not be a symlink"]
    try: text=path.read_text(encoding="utf-8")
    except (OSError,UnicodeError) as exc: return [f"cannot read registry: {exc}"]
    rows,errors=_rows(text); names=set(); root=project_root.resolve() if project_root else None
    for number,cells in rows:
        name,trigger,lifecycle,workflow,inputs,outputs,reviewer,required,location,version,content_id,missing=cells
        if not NAME_RE.fullmatch(name): errors.append(f"line {number}: invalid skill name {name!r}")
        elif name in names: errors.append(f"line {number}: duplicate skill name {name}")
        names.add(name)
        for label,value in (("trigger",trigger),("lifecycle",lifecycle),("workflow stages",workflow),("inputs",inputs),("outputs/evidence",outputs),("reviewer/gate",reviewer),("missing-capability",missing)):
            if not value: errors.append(f"line {number}: {label} is empty")
        if workflow:
            stages=[stage.strip() for stage in workflow.split(',')]
            if not all(stages): errors.append(f"line {number}: workflow stages contains empty stage")
            if any(stage.lower() in STATUSES for stage in stages):
                errors.append(f"line {number}: workflow stages must describe invocation, not lifecycle")
        if required not in REQUIRED: errors.append(f"line {number}: required must be required or optional")
        target_path=Path(location)
        if not location or target_path.is_absolute() or ".." in target_path.parts:
            errors.append(f"line {number}: location must be relative and stay in the project"); continue
        if not VERSION_RE.fullmatch(version): errors.append(f"line {number}: invalid semantic version {version!r}")
        if not CONTENT_ID_RE.fullmatch(content_id): errors.append(f"line {number}: content-id must be sha256:<64 lowercase hex>")
        if lifecycle not in STATUSES: errors.append(f"line {number}: lifecycle must be active, staged, or retired")
        if root is None: continue
        target=project_root / target_path
        try:
            resolved=target.resolve(strict=False)
            if resolved != root and root not in resolved.parents: errors.append(f"line {number}: location escapes project root")
            if target.is_symlink(): errors.append(f"line {number}: location must not be a symlink")
            if lifecycle in {"active", "staged"} and not target.exists(): errors.append(f"line {number}: {lifecycle} skill path does not exist")
            if lifecycle in {"active", "staged"} and target.exists() and not target.is_dir(): errors.append(f"line {number}: skill location must be a directory")
            if target.exists() and target.is_dir():
                actual="sha256:"+_tree_digest(target)
                # Never print the current digest: pasting it into the row would
                # record an unreviewed tree as reviewed.
                if CONTENT_ID_RE.fullmatch(content_id) and content_id != actual:
                    errors.append(f"line {number}: stale content-id: {name} changed since review; unavailable until its "
                                  "reviewer gate re-passes and the owner records the newly reviewed digest")
                skill=target/"SKILL.md"
                if lifecycle in {"active", "staged"} and not skill.is_file():
                    errors.append(f"line {number}: skill location missing SKILL.md")
                if skill.is_file():
                    first=skill.read_text(encoding="utf-8",errors="replace").splitlines(); front_name=next((ln.split(":",1)[1].strip() for ln in first if ln.startswith("name:")),"")
                    if front_name != name: errors.append(f"line {number}: target SKILL.md name does not match registry name")
        except (OSError,RuntimeError,ValueError) as exc: errors.append(f"line {number}: cannot inspect location: {exc}")
    return errors

def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__+" An absent registry is valid (SKIP, exit 0).")
    parser.add_argument("root",type=Path,help="project root; registry Location cells are relative to it")
    where=parser.add_mutually_exclusive_group()
    where.add_argument("--registry",metavar="FILE",help="explicit SKILL-REGISTRY.md file, relative to the project root or absolute")
    where.add_argument("--register-dir",metavar="PATH",help="directory holding SKILL-REGISTRY.md, relative to the project root or absolute; "
                       "default: <root>/docs, then <root>")
    parser.add_argument("--digest",metavar="LOCATION",help="print the tree digest of LOCATION (relative to the project root) for a reviewer "
                        "to record after review; the printed digest is not an approval")
    args=parser.parse_args(argv)
    if args.digest is not None:
        target=Path(args.digest) if Path(args.digest).is_absolute() else args.root/args.digest
        if not target.is_dir() or target.is_symlink():
            print(f"FAIL skill-registry: digest location is not a real directory: {args.digest}"); return 1
        try: value=_tree_digest(target)
        except ValueError as exc: print(f"FAIL skill-registry: {exc}"); return 1
        print(f"DIGEST {args.digest}: sha256:{value} (unreviewed: record it only after the reviewer gate passes)"); return 0
    try: path=_registry_path(args.root,args.registry,args.register_dir)
    except ValueError as exc: print(f"FAIL skill-registry: {exc}"); return 1
    if path is None:
        where_absent=f" in {args.register_dir}" if args.register_dir is not None else ""
        print(f"SKIP skill-registry: SKILL-REGISTRY.md absent{where_absent}"); return 0
    errors=validate(path,args.root)
    if errors:
        for error in errors: print(f"FAIL skill-registry: {error}")
        return 1
    print(f"PASS skill-registry: {path}"); return 0
if __name__ == "__main__": raise SystemExit(main())
