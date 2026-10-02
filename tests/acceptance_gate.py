"""Fail-closed validator for the bounded hardening acceptance bundle.

This is intentionally a small gate, rather than a test runner.  It validates
the structured result emitted by a child runner against a reviewed case
manifest and runtime hash manifest.  A nonzero child exit is only acceptable
when every declared case has its independently expected rejection and exit.
"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import re
import subprocess

HASH_RE = re.compile(r"^[a-f0-9]{64}$")
CANONICAL_SCOPE = "core-doctor-migration"


def canonical_hash_keys(subject_root: Path) -> set[str]:
    """Return the complete, trusted input scope for the canonical bundle."""
    try:
        from input_manifest import required_paths
    except ModuleNotFoundError:
        from tests.input_manifest import required_paths
    return required_paths(subject_root)


class GateError(ValueError):
    pass


def validate_result(result: Mapping, expected_cases: Mapping[str, Mapping],
                    runtime_hashes: Mapping[str, str], *, strict: bool = False) -> None:
    """Raise ``GateError`` for malformed, incomplete, or false-green output."""
    if not isinstance(result, Mapping):
        raise GateError("result must be an object")
    if type(result.get("successful")) is not bool:
        raise GateError("successful must be a boolean")
    if type(result.get("exit_code")) is not int or isinstance(result.get("exit_code"), bool):
        raise GateError("aggregate exit_code must be an integer")
    if result.get("successful") is not True:
        if result.get("exit_code") == 0:
            raise GateError("failed acceptance child must have nonzero exit code")
        failures = result.get("failures")
        if not isinstance(failures, list) or not failures:
            raise GateError("failed acceptance child must carry a diagnostic failure")
        raise GateError("current acceptance child did not report success")
    if result.get("exit_code") != 0:
        raise GateError("successful result must have exit code 0")
    for key in ("tests", "failures", "errors", "skips", "expected_failures", "cases", "runtime_hashes"):
        if key not in result:
            raise GateError(f"missing result field: {key}")
    if type(result["tests"]) is not int or isinstance(result["tests"], bool) or result["tests"] <= 0:
        raise GateError("empty or invalid discovery")
    for key in ("failures", "errors", "skips"):
        if not isinstance(result[key], list) or result[key]:
            raise GateError(f"unexpected {key}")
    if not isinstance(result["expected_failures"], list) or result["expected_failures"]:
        raise GateError("expected-failure markers are not accepted")
    if result["runtime_hashes"] != dict(runtime_hashes):
        raise GateError("runtime hash manifest mismatch")
    if not isinstance(result["runtime_hashes"], Mapping):
        raise GateError("runtime hashes must be path-to-SHA256 strings")
    if strict and (result.get("evidence_scope") != CANONICAL_SCOPE):
        raise GateError("canonical evidence scope is missing or untrusted")
    if any(not isinstance(path, str) or not isinstance(value, str) or
           (strict and not HASH_RE.fullmatch(value))
           for path, value in result["runtime_hashes"].items()):
        raise GateError("runtime hashes must be path-to-SHA256 strings")
    cases = result["cases"]
    if not isinstance(cases, list):
        raise GateError("cases must be a list")
    if not expected_cases:
        raise GateError("empty expected case manifest")
    if result["tests"] != len(cases):
        raise GateError("discovery total does not match case count")
    for expected_id, expected in expected_cases.items():
        if not isinstance(expected_id, str) or not isinstance(expected, Mapping):
            raise GateError("malformed expected case manifest")
        for key in ("outcome", "exit_code", "assertion"):
            if key not in expected:
                raise GateError(f"expected case lacks {key}: {expected_id}")
    seen = set()
    for case in cases:
        if not isinstance(case, Mapping) or not isinstance(case.get("id"), str):
            raise GateError("malformed case record")
        case_id = case["id"]
        if case_id in seen:
            raise GateError(f"duplicate case: {case_id}")
        seen.add(case_id)
        expected = expected_cases.get(case_id)
        if expected is None:
            raise GateError(f"unexpected case: {case_id}")
        if case.get("outcome") != expected.get("outcome"):
            raise GateError(f"wrong outcome for {case_id}")
        if type(case.get("exit_code")) is not int or case.get("exit_code") != expected.get("exit_code"):
            raise GateError(f"wrong exit for {case_id}")
        if case.get("assertion") != expected.get("assertion"):
            raise GateError(f"case lacks its required behavioral assertion: {case_id}")
    missing = set(expected_cases) - seen
    if missing:
        raise GateError("missing cases: " + ", ".join(sorted(missing)))
    if strict:
        try:
            try:
                from acceptance_evidence import validate_canonical
            except ModuleNotFoundError:
                from tests.acceptance_evidence import validate_canonical
            validate_canonical(result, expected_cases)
        except (ValueError, OSError, subprocess.CalledProcessError) as error:
            raise GateError(str(error)) from error


def validate_json(result, expected_cases, runtime_hashes, *, strict: bool = False):
    """JSON-friendly wrapper used by the command-line evidence checker."""
    validate_result(result, expected_cases, runtime_hashes, strict=strict)
    return {"accepted": True, "cases": len(expected_cases)}
