#!/usr/bin/env python3
"""Validate one recorded acceptance-child result (fail closed).

Run it isolated: ``python3 -I -B tests/validate_acceptance.py [options] RESULT CASES HASHES``.
Before it judges anything it hashes the judging files named in ``tests/harness.sha256`` from
their bytes, refuses any difference, and compiles the judging modules from those same bytes
rather than through the import system, so a planted module, bytecode cache or path entry in the
reviewed tree cannot stand in for them (D-0026). Only the standard library is imported here.

``--subject-root PATH`` makes this checkout the judge of another tree: contract, fixtures and
templates come from here, the hash scope, Git state and runtime root from PATH. Run that from a
checkout the reviewer already trusts, with ``--harness-sha256`` computed outside the candidate.
"""
import hashlib
import json
import os
import sys
import sysconfig
import types
from pathlib import Path

JUDGE = Path(__file__).resolve().parents[1]
RECORD = "tests/harness.sha256"
# The files this validator requires the record to list; an audit test keeps this equal to
# input_manifest.HARNESS_FILES and to what a run actually opens.
MODULE_FILES = {"input_manifest": "tests/input_manifest.py",
                "acceptance_evidence": "tests/acceptance_evidence.py",
                "acceptance_gate": "tests/acceptance_gate.py"}
HARNESS_PATHS = frozenset(MODULE_FILES.values()) | {
    "tests/validate_acceptance.py", "tests/run_acceptance.py",
    "tests/fixtures/hardening-2026-09-12/acceptance-cases.json",
    "tests/fixtures/acceptance-v2/contract.json", "templates/LEDGER.md",
    "tests/fixtures/hardening-2026-09-12/cases/doctor-a1-positive.md",
    "tests/fixtures/hardening-2026-09-12/cases/doctor-a1.md",
    "tests/fixtures/hardening-2026-09-12/cases/doctor-a2-positive.md",
    "tests/fixtures/hardening-2026-09-12/cases/doctor-a2.md",
    "tests/fixtures/hardening-2026-09-12/cases/migration-split-cdata.md",
    "tests/fixtures/hardening-2026-09-12/cases/migration-split-pi.md",
    "tests/fixtures/acceptance-v2/contiguous-cdata.md", "tests/fixtures/acceptance-v2/contiguous-pi.md",
    "tests/fixtures/migration-20/STATUS.md"}
M = types.SimpleNamespace()  # GateError, validate_json, load_json: bound only after verification


class Refusal(ValueError):
    pass


def verified_bytes(root, pinned=None):
    """Return ({path: bytes}, digest) for the judging files, or raise Refusal."""
    try:
        recorded = (root / RECORD).read_bytes()
    except OSError:
        raise Refusal("harness digest record missing or unreadable: " + RECORD) from None
    try:
        lines = recorded.decode("utf-8").splitlines(keepends=True)
        entries = [line[:-1].rsplit(":", 1) for line in lines]
    except UnicodeDecodeError:
        entries = []
    if (not entries or any(not line.endswith("\n") for line in lines) or
            any(len(e) != 2 or len(e[1]) != 64 or any(c not in "0123456789abcdef" for c in e[1])
                for e in entries) or [e[0] for e in entries] != sorted(e[0] for e in entries) or
            {e[0] for e in entries} != HARNESS_PATHS or len(entries) != len(HARNESS_PATHS)):
        raise Refusal("harness digest record is malformed or lists the wrong files")
    blobs = {}
    for path, digest in entries:
        try:
            blobs[path] = (root / path).read_bytes()
        except OSError:
            raise Refusal("harness file missing or unreadable: " + path) from None
        if hashlib.sha256(blobs[path]).hexdigest() != digest:
            raise Refusal("harness digest does not match its record: judging code or inputs changed (" + path + ")")
    digest = hashlib.sha256(recorded).hexdigest()
    if pinned is not None and pinned != digest:
        raise Refusal("harness digest does not match the reviewer pin")
    return blobs, digest


def load_judging_modules(root, blobs):
    for name in ("input_manifest", "acceptance_evidence", "acceptance_gate"):
        path = MODULE_FILES[name]
        module = types.ModuleType(name)
        module.__file__ = str(root / path)
        sys.modules[name] = module
        exec(compile(blobs[path], module.__file__, "exec"), module.__dict__)
    M.GateError = sys.modules["acceptance_gate"].GateError
    M.validate_json = sys.modules["acceptance_gate"].validate_json
    M.load_json = sys.modules["acceptance_evidence"].load_json


def inside(path, root):
    return path == root or str(path).startswith(str(root) + os.sep)


def check_origins(*roots):
    """Refuse a loaded module or search-path entry that lives in a reviewed tree, and any
    standard-library name that did not come from the standard library."""
    real = lambda value: Path(os.path.realpath(value))
    library = [real(sysconfig.get_path(key)) for key in ("stdlib", "platstdlib")]
    trusted = {str(real(JUDGE / MODULE_FILES[name])) for name in MODULE_FILES}
    trusted.add(str(real(Path(__file__))))  # this validator, already hashed against the record
    roots = [real(r) for r in roots]
    for entry in sys.path:
        where = real(entry or os.getcwd())
        if not any(inside(where, lib) for lib in library) and any(inside(where, r) for r in roots):
            raise Refusal("search path entry inside the reviewed tree: " + str(entry))
    for name, module in list(sys.modules.items()):
        origin = getattr(module, "__file__", None)
        if not origin or str(real(origin)) in trusted:
            continue
        where = real(origin)
        in_library = any(inside(where, lib) for lib in library)
        if name.split(".")[0] in sys.stdlib_module_names and not in_library:
            raise Refusal("standard-library module shadowed: " + name + " from " + str(origin))
        if not in_library and any(inside(where, r) for r in roots):
            raise Refusal("module loaded from the reviewed tree: " + name + " from " + str(origin))
    for name in MODULE_FILES:
        if getattr(sys.modules.get(name), "__file__", None) != str(JUDGE / MODULE_FILES[name]):
            raise Refusal("judging module was replaced: " + name)


def validate_manifest_file(path):
    data = M.load_json(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or type(data.get("version")) is not int or data.get("version") != 1 or not isinstance(data.get("cases"), list) or not data["cases"]:
        raise M.GateError("frozen acceptance manifest is empty or has an unsupported version")
    seen = set()
    for case in data["cases"]:
        required = ("id", "fixture", "fixture_sha256", "classification", "inventory",
                    "write", "exit", "positive", "scope", "assertion")
        if not isinstance(case, dict) or any(key not in case for key in required):
            raise M.GateError("frozen acceptance case schema is incomplete")
        ident = case["id"]
        if not isinstance(ident, str) or not ident or ident in seen:
            raise M.GateError("frozen acceptance case ids must be unique and nonempty")
        seen.add(ident)
        if type(case["exit"]) is not int or isinstance(case["exit"], bool) or case["exit"] not in (0, 1, 2):
            raise M.GateError(f"invalid expected exit for {ident}")
        fixture = path.parent / case["fixture"]
        if not fixture.is_file():
            raise M.GateError(f"missing frozen fixture: {ident}")
        if hashlib.sha256(fixture.read_bytes()).hexdigest() != case["fixture_sha256"]:
            raise M.GateError(f"frozen fixture hash mismatch: {ident}")
    return data


def take_option(argv, flag):
    if flag not in argv:
        return None
    at = argv.index(flag)
    if at + 1 >= len(argv):
        print("usage: " + flag + " needs a value", file=sys.stderr)
        raise SystemExit(2)
    value = argv[at + 1]
    del argv[at:at + 2]
    return value


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    pinned = take_option(argv, "--harness-sha256")
    candidate_pin = take_option(argv, "--candidate-harness-sha256")
    subject_option = take_option(argv, "--subject-root")
    if len(argv) != 3:
        print("usage: python3 -I -B validate_acceptance.py [--harness-sha256 DIGEST] [--subject-root PATH] "
              "[--candidate-harness-sha256 DIGEST] RESULT.json CASES.json HASHES.json", file=sys.stderr)
        return 2
    subject = Path(subject_option).resolve() if subject_option else JUDGE
    try:
        if not (sys.flags.isolated and sys.flags.dont_write_bytecode):
            raise Refusal("run isolated: python3 -I -B tests/validate_acceptance.py ...")
        blobs, digest = verified_bytes(JUDGE, pinned)
        load_judging_modules(JUDGE, blobs)
        sys.modules["acceptance_evidence"].SUBJECT = subject
        check_origins(JUDGE, subject)
    except (Refusal, OSError, SyntaxError) as error:
        print(f"REJECT: {error}", file=sys.stderr)
        return 1
    canonical_cases = (JUDGE / "tests/fixtures/hardening-2026-09-12/acceptance-cases.json").resolve()
    if Path(argv[1]).resolve() != canonical_cases:
        print("REJECT: expected case manifest is not the frozen reviewed bundle", file=sys.stderr)
        return 1
    try:
        result = M.load_json(Path(argv[0]).read_text(encoding="utf-8"))
        cases = validate_manifest_file(Path(argv[1]))
        hashes = M.load_json(Path(argv[2]).read_text(encoding="utf-8"))
        if not isinstance(hashes, dict) or any(not isinstance(k, str) or not isinstance(v, str) or len(v) != 64 for k, v in hashes.items()):
            raise M.GateError("runtime hash input must be a path-to-hash object")
        raw_cases = cases.get("cases", cases)
        if isinstance(raw_cases, list):
            expected = {
                item["id"]: {
                    "outcome": "reject" if int(item["exit"]) else "accept",
                    "exit_code": int(item["exit"]),
                    "assertion": item.get("assertion", "behavioral-contract"),
                }
                for item in raw_cases
            }
        else:
            expected = raw_cases
        # The frozen manifest path is the trusted invocation boundary.  This
        # explicitly selects canonical strict mode; result fields and the
        # producer-supplied hash scope never select or downgrade strictness.
        accepted = M.validate_json(result, expected, hashes, strict=True)
        if subject != JUDGE:
            candidate = sys.modules["input_manifest"].harness_digest(subject)
            if candidate_pin is not None and candidate != candidate_pin:
                raise M.GateError("candidate harness digest does not match the reviewer pin")
            accepted = dict(accepted, subject_root=str(subject), candidate_harness_sha256=candidate,
                            candidate_harness_matches_judge=candidate == digest)
        check_origins(JUDGE, subject)
    except (OSError, ValueError, TypeError, json.JSONDecodeError, M.GateError) as error:
        print(f"REJECT: {error}", file=sys.stderr)
        return 1
    print(json.dumps(accepted, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
