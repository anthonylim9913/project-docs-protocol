#!/usr/bin/env python3
"""Validate one recorded acceptance-child result (fail closed).

The judging code is loaded only from bytes that match `tests/harness.sha256`, in an
isolated interpreter (`-I -B`), never through `sys.path` (D-0025). Run from a checkout
you trust with `--subject-root CANDIDATE`, it judges a separate candidate tree without
importing any of the candidate's code; that is the external check. Run inside the tree
it judges, the same checks are a convenience: code in a tree cannot vouch for itself.
"""
import sys

if __name__ == "__main__" and not (sys.flags.isolated and sys.flags.dont_write_bytecode):
    # Before any import that searches sys.path: re-run isolated, so a module planted beside
    # this script (tests/json.py, tests/acceptance_gate/) is never found, and no bytecode
    # is written. os is already loaded at interpreter startup; this import binds that module.
    import os
    os.execv(sys.executable, [sys.executable, "-I", "-B", __file__] + sys.argv[1:])

import hashlib
import re
import types
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RECORD = "tests/harness.sha256"
# Loaded in this order from verified bytes; each later module finds the earlier ones in
# sys.modules, so their `from input_manifest import ...` never searches a path.
MODULES = ("input_manifest", "acceptance_evidence", "acceptance_gate")
ENTRY_POINTS = ("validate_acceptance", "run_acceptance")
CASES = "tests/fixtures/hardening-2026-09-12/acceptance-cases.json"
# The record may list more (input_manifest.HARNESS_FILES is the full set); it may not list less.
REQUIRED = {"tests/%s.py" % name for name in MODULES + ENTRY_POINTS} | {CASES, "tests/fixtures/acceptance-v2/contract.json"}
BYTECODE = (".pyc", ".pyo", ".so", ".pyd", ".pth")
LINE = re.compile(r"([0-9a-f]{64})  ([^\n]+)")


class HarnessError(ValueError):
    pass


def _safe(name):
    parts = name.split("/")
    return (not PurePosixPath(name).is_absolute() and not any(c in name for c in "\\:\r\0")
            and all(p not in ("", ".", "..") for p in parts))


def read_record(root, pinned=None):
    """Return {path: sha256} from the record, after checking the reviewer pin over its bytes."""
    try:
        raw = (root / RECORD).read_bytes()
    except OSError as error:
        raise HarnessError("harness record missing or unreadable: " + RECORD) from error
    if pinned is not None and (not re.fullmatch("[0-9a-f]{64}", pinned) or hashlib.sha256(raw).hexdigest() != pinned):
        raise HarnessError("harness record does not match the reviewer pin")
    entries = {}
    for line in raw.decode("utf-8", "replace").splitlines():
        match = LINE.fullmatch(line)
        if not match or not _safe(match.group(2)) or match.group(2) in entries:
            raise HarnessError("harness record is malformed: " + RECORD)
        entries[match.group(2)] = match.group(1)
    missing = sorted(REQUIRED - set(entries))
    if missing:
        raise HarnessError("harness record omits judging files: " + ", ".join(missing))
    return entries


def verified_bytes(root, entries):
    """Read each harness file once; the bytes returned are the bytes that were hashed."""
    blobs, changed = {}, []
    for name in sorted(entries):
        path = root / name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if root in p.parents):
            raise HarnessError("harness file is linked: " + name)
        try:
            blobs[name] = path.read_bytes()
        except OSError as error:
            raise HarnessError("harness file missing or unreadable: " + name) from error
        if hashlib.sha256(blobs[name]).hexdigest() != entries[name]:
            changed.append(name)
    if changed:
        raise HarnessError("harness files do not match " + RECORD + ": " + ", ".join(changed))
    return blobs


def shadowing(root):
    """Paths in tests/ that Python could import in place of a harness or stdlib module."""
    stdlib = set(getattr(sys, "stdlib_module_names", ())) | set(sys.builtin_module_names)
    found = []
    for entry in sorted((root / "tests").iterdir()):
        stem = entry.name.split(".")[0]
        if entry.name == "__pycache__" or entry.name.endswith(BYTECODE):
            found.append(entry.name)
        elif stem in stdlib and (entry.is_dir() or entry.suffix == ".py"):
            found.append(entry.name)
        elif stem in MODULES + ENTRY_POINTS and entry.name != stem + ".py":
            found.append(entry.name)
    return ["tests/" + name for name in found]


def load_harness(root=ROOT, pinned=None):
    """Verify the harness in `root` and load its modules from the verified bytes.

    Returns (modules, entries). Raises HarnessError before any module is executed if a
    file differs from the record or the record from the pin, and afterwards if any loaded
    module inside `root` is not the one expected from its own .py path.
    """
    entries = read_record(root, pinned)
    planted = shadowing(root)
    if planted:
        raise HarnessError("module or bytecode in tests/ could shadow the harness: " + ", ".join(planted))
    blobs = verified_bytes(root, entries)
    modules = {}
    for name in MODULES:
        relative = "tests/" + name + ".py"
        module = types.ModuleType(name)
        module.__file__ = str(root / relative)
        sys.modules[name] = modules[name] = module
        exec(compile(blobs[relative], module.__file__, "exec", dont_inherit=True), module.__dict__)
    check_origins(root, modules)
    return modules, entries


def check_origins(root, modules):
    expected = {str(root / ("tests/" + name + ".py")) for name in MODULES + ENTRY_POINTS}
    for name, module in list(sys.modules.items()):
        origin = getattr(module, "__file__", None)
        if not isinstance(origin, str):
            continue
        resolved = Path(origin).resolve()
        if (resolved == root or root in resolved.parents) and str(resolved) not in expected:
            raise HarnessError("module %s was loaded from an unexpected path: %s" % (name, origin))
    for name, module in modules.items():
        if sys.modules.get(name) is not module or module.__file__ != str(root / ("tests/" + name + ".py")):
            raise HarnessError("harness module was replaced after loading: " + name)


def check_subject_harness(subject, entries):
    """A separate candidate's judging files must be byte-identical to the trusted ones."""
    differ = []
    for name in sorted(set(entries) | {RECORD}):
        trusted = (ROOT / name).read_bytes()
        try:
            other = (subject / name).read_bytes()
        except OSError:
            other = None
        if other != trusted:
            differ.append(name)
    planted = shadowing(subject)
    if differ or planted:
        raise HarnessError("candidate judging files differ from the trusted checkout: " + ", ".join(differ + planted))


def validate_manifest_file(path, load_json, GateError):
    data = load_json(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or type(data.get("version")) is not int or data.get("version") != 1 or not isinstance(data.get("cases"), list) or not data["cases"]:
        raise GateError("frozen acceptance manifest is empty or has an unsupported version")
    seen = set()
    for case in data["cases"]:
        required = ("id", "fixture", "fixture_sha256", "classification", "inventory",
                    "write", "exit", "positive", "scope", "assertion")
        if not isinstance(case, dict) or any(key not in case for key in required):
            raise GateError("frozen acceptance case schema is incomplete")
        ident = case["id"]
        if not isinstance(ident, str) or not ident or ident in seen:
            raise GateError("frozen acceptance case ids must be unique and nonempty")
        seen.add(ident)
        if type(case["exit"]) is not int or isinstance(case["exit"], bool) or case["exit"] not in (0, 1, 2):
            raise GateError(f"invalid expected exit for {ident}")
        fixture = path.parent / case["fixture"]
        if not fixture.is_file():
            raise GateError(f"missing frozen fixture: {ident}")
        if hashlib.sha256(fixture.read_bytes()).hexdigest() != case["fixture_sha256"]:
            raise GateError(f"frozen fixture hash mismatch: {ident}")
    return data


def main(argv=None):
    import argparse
    import json
    parser = argparse.ArgumentParser(description="Validate one acceptance-child result; fail closed.")
    parser.add_argument("--harness-sha256", metavar="DIGEST",
                        help="reviewer pin: SHA-256 of tests/harness.sha256, computed outside this program")
    parser.add_argument("--subject-root", type=Path, metavar="DIR",
                        help="judge this separate candidate checkout; this checkout's code does the judging")
    parser.add_argument("result", type=Path)
    parser.add_argument("cases", type=Path)
    parser.add_argument("hashes", type=Path)
    args = parser.parse_args(argv)
    try:
        # Before any verdict: the code about to judge must be the code that was recorded.
        modules, entries = load_harness(ROOT, args.harness_sha256)
        subject = ROOT if args.subject_root is None else args.subject_root.resolve()
        if subject != ROOT:
            check_subject_harness(subject, entries)
    except (HarnessError, OSError) as error:
        print(f"REJECT: {error}", file=sys.stderr)
        return 1
    GateError, validate_json = modules["acceptance_gate"].GateError, modules["acceptance_gate"].validate_json
    load_json = modules["acceptance_evidence"].load_json
    canonical_cases = (ROOT / CASES).resolve()
    if args.cases.resolve() != canonical_cases:
        print("REJECT: expected case manifest is not the frozen reviewed bundle", file=sys.stderr)
        return 1
    try:
        result = load_json(args.result.read_text(encoding="utf-8"))
        cases = validate_manifest_file(args.cases, load_json, GateError)
        hashes = load_json(args.hashes.read_text(encoding="utf-8"))
        if not isinstance(hashes, dict) or any(not isinstance(k, str) or not isinstance(v, str) or len(v) != 64 for k, v in hashes.items()):
            raise GateError("runtime hash input must be a path-to-hash object")
        expected = {
            item["id"]: {
                "outcome": "reject" if int(item["exit"]) else "accept",
                "exit_code": int(item["exit"]),
                "assertion": item.get("assertion", "behavioral-contract"),
            }
            for item in cases["cases"]
        }
        # The frozen manifest path is the trusted invocation boundary.  This
        # explicitly selects canonical strict mode; result fields and the
        # producer-supplied hash scope never select or downgrade strictness.
        accepted = validate_json(result, expected, hashes, strict=True, subject_root=subject)
    except (OSError, ValueError, TypeError, json.JSONDecodeError, GateError) as error:
        print(f"REJECT: {error}", file=sys.stderr)
        return 1
    print(json.dumps(accepted, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
