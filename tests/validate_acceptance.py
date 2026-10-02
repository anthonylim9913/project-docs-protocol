#!/usr/bin/env python3
"""Validate one recorded acceptance-child result (fail closed)."""
import json
import hashlib
import sys
from pathlib import Path

try:
    from acceptance_gate import GateError, validate_json
    from acceptance_evidence import load_json
except ModuleNotFoundError:
    from tests.acceptance_gate import GateError, validate_json
    from tests.acceptance_evidence import load_json


def validate_manifest_file(path):
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
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 3:
        print("usage: validate_acceptance.py RESULT.json CASES.json HASHES.json", file=sys.stderr)
        return 2
    canonical_cases = (Path(__file__).parent / "fixtures/hardening-2026-09-12/acceptance-cases.json").resolve()
    if Path(argv[1]).resolve() != canonical_cases:
        print("REJECT: expected case manifest is not the frozen reviewed bundle", file=sys.stderr)
        return 1
    try:
        result = load_json(Path(argv[0]).read_text(encoding="utf-8"))
        cases = validate_manifest_file(Path(argv[1]))
        hashes = load_json(Path(argv[2]).read_text(encoding="utf-8"))
        if not isinstance(hashes, dict) or any(not isinstance(k, str) or not isinstance(v, str) or len(v) != 64 for k, v in hashes.items()):
            raise GateError("runtime hash input must be a path-to-hash object")
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
        accepted = validate_json(result, expected, hashes, strict=True)
    except (OSError, ValueError, TypeError, json.JSONDecodeError, GateError) as error:
        print(f"REJECT: {error}", file=sys.stderr)
        return 1
    print(json.dumps(accepted, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
