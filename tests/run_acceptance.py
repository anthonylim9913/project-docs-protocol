#!/usr/bin/env python3
"""Run and validate the frozen hardening acceptance bundle.

The runner deliberately executes the real command-line tools in disposable
projects.  It emits the child result even when validation rejects it so a
mutant run retains the semantic observation that caused rejection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from collections.abc import Mapping

try:
    from acceptance_gate import GateError, validate_result
    from input_manifest import hashes, dirty_inputs
except ModuleNotFoundError:  # imported as tests.run_acceptance by unit tests
    from tests.acceptance_gate import GateError, validate_result
    from tests.input_manifest import hashes, dirty_inputs


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "tests/fixtures/hardening-2026-09-12"
MANIFEST = BUNDLE / "acceptance-cases.json"
TODAY = "2026-09-14"


def runtime_hashes(runtime_root: Path) -> dict[str, str]:
    return hashes(runtime_root.resolve())


def verify_manifest(manifest: Mapping) -> None:
    if manifest.get("version") != 1 or not isinstance(manifest.get("cases"), list) or not manifest["cases"]:
        raise GateError("frozen acceptance manifest must have version 1 and nonempty cases")
    ids = set()
    for case in manifest["cases"]:
        required = ("id", "fixture", "fixture_sha256", "classification", "inventory",
                    "write", "exit", "positive", "scope", "assertion")
        if not isinstance(case, Mapping) or any(key not in case for key in required):
            raise GateError("malformed frozen acceptance case")
        case_id = case["id"]
        if not isinstance(case_id, str) or not case_id or case_id in ids:
            raise GateError("duplicate or empty frozen acceptance case id")
        ids.add(case_id)
        if type(case["exit"]) is not int or isinstance(case["exit"], bool) or case["exit"] not in (0, 1, 2):
            raise GateError(f"invalid expected exit for {case_id}")
        fixture = BUNDLE / case["fixture"]
        if not fixture.is_file() or hashlib.sha256(fixture.read_bytes()).hexdigest() != case["fixture_sha256"]:
            raise GateError(f"frozen fixture hash mismatch: {case_id}")
        if not isinstance(case["positive"], str) or not case["positive"].strip():
            raise GateError(f"missing positive control: {case_id}")


def seed_register(project: Path) -> None:
    docs = project / "docs"
    docs.mkdir(parents=True)
    (docs / "README.md").write_text(
        "*Installed via the `project-docs-protocol` skill.*\n", encoding="utf-8"
    )
    (docs / "STATUS.md").write_text(
        f"# STATUS\n\nLast updated: {TODAY}\n\n## Current phase\n\nFixture review.\n",
        encoding="utf-8",
    )
    (docs / "CHANGELOG.md").write_text(
        f"# CHANGELOG\n\n## {TODAY} — initialized project documentation system\n\nInstalled.\n",
        encoding="utf-8",
    )
    (docs / "DECISIONS.md").write_text("# DECISIONS\n", encoding="utf-8")


def snapshot(project: Path) -> dict[str, str]:
    return {path.relative_to(project).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in project.rglob("*") if path.is_file()}


def tree_hash(hashes: Mapping[str, str]) -> str:
    material = "\n".join(f"{key}:{hashes[key]}" for key in sorted(hashes)) + "\n"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def git_provenance(root: Path, supplied: str) -> dict:
    try:
        head = subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
        dirty = dirty_inputs(root)
    except (OSError, subprocess.CalledProcessError):
        return {"runtime_tree_sha256": "", "verified": False,
                "source_commit_argument": supplied, "git_head": "", "dirty": True}
    return {"runtime_tree_sha256": "", "verified": bool(head == supplied and not dirty),
            "source_commit_argument": supplied, "git_head": head, "dirty": bool(dirty)}


def run_case(case: dict, runtime_root: Path, scratch: Path) -> dict:
    case_id = case["id"]
    project = scratch / case_id
    seed_register(project)
    fixture = (BUNDLE / case["fixture"]).read_text(encoding="utf-8")
    commands: list[list[str]] = []
    outputs: list[subprocess.CompletedProcess[str]] = []
    stages: list[dict] = []
    before = None
    plan = project / "plan.json"
    if case_id.startswith("doctor-"):
        (project / "AGENTS.md").write_text(fixture, encoding="utf-8")
        before = snapshot(project)
        command = [sys.executable, "-B", str(runtime_root / "scripts/docs-doctor.py"),
                   str(project), "--today", TODAY, "--no-git"]
        commands.append(command)
        outputs.append(subprocess.run(command, cwd=runtime_root, capture_output=True,
                                      text=True, timeout=15))
        output = outputs[-1]
        stages.append({"name": "doctor", "exit_code": output.returncode,
                       "stdout": output.stdout, "stderr": output.stderr,
                       "reason": "wiring-block" if output.returncode == 2 else "unexpected"})
        wiring = ""
        for line in output.stdout.splitlines():
            if line.endswith("wiring-block") or "wiring-block" in line:
                wiring = line.strip()
                break
        fields = wiring.split()
        expected = output.returncode == 2 and len(fields) >= 2 and fields[:2] == ["FAIL", "wiring-block"]
        assertion = "wiring-block=FAIL" if expected else f"observed:{wiring or 'missing'}"
        targeted = case_id if not expected else ""
        semantic = expected
        positive = run_positive_doctor(case, runtime_root, scratch)
    else:
        (project / "docs/STATUS.md").write_text(fixture, encoding="utf-8")
        before = snapshot(project)
        preview = [sys.executable, "-B", str(runtime_root / "scripts/docs-migrate.py"),
                   str(project), "--register-dir", "docs", "--plan", str(plan),
                   "--today", TODAY]
        commands.append(preview)
        outputs.append(subprocess.run(preview, cwd=runtime_root, capture_output=True,
                                      text=True, timeout=15))
        stages.append({"name": "preview", "exit_code": outputs[-1].returncode,
                       "stdout": outputs[-1].stdout, "stderr": outputs[-1].stderr,
                       "reason": "preview-success" if outputs[-1].returncode == 0 else "preview-refused"})
        counts = {}
        if plan.is_file():
            counts = json.loads(plan.read_text(encoding="utf-8")).get("counts", {})
        write = [sys.executable, "-B", str(runtime_root / "scripts/docs-migrate.py"),
                 str(project), "--register-dir", "docs", "--plan", str(plan),
                 "--today", TODAY, "--write"]
        commands.append(write)
        outputs.append(subprocess.run(write, cwd=runtime_root, capture_output=True,
                                      text=True, timeout=15))
        stages.append({"name": "write", "exit_code": outputs[-1].returncode,
                       "stdout": outputs[-1].stdout, "stderr": outputs[-1].stderr,
                       "reason": "unmapped-disposition" if outputs[-1].returncode == 2 else "unexpected"})
        output = outputs[-1]
        expected_counts = {"source_records": 1, "mapped_records": 0,
                           "new_rows": 0, "unmapped_records": 1}
        semantic = all(counts.get(key) == value for key, value in expected_counts.items()) \
            and output.returncode == 2 and not (
            project / "docs/.docs-migrate-journal.json"
        ).exists()
        assertion = (
            "opaque-refusal-before-write" if semantic
            else "opaque-inventory-mismatch"
        )
        targeted = "" if semantic else case_id
        wiring = ""
        positive = run_positive_delimiter(case, runtime_root, scratch)

    exit_code = outputs[-1].returncode
    return {
        "id": case_id,
        "outcome": "reject" if semantic else "accept",
        "exit_code": exit_code,
        "assertion": assertion,
        "targeted_case": targeted or case_id,
        "targeted_behavior": case.get("classification", ""),
        "commands": commands,
        "project": str(project),
        "runtime_hashes": runtime_hashes(runtime_root),
        "stages": stages,
        "protected_state": {
            "before": before,
            "after": snapshot(project),
            "unchanged": all(before.get(name) == snapshot(project).get(name) for name in before
                              if name != "plan.json"),
            "unauthorized_files": sorted(set(snapshot(project)) - set(before) - {"plan.json"}),
        },
        "positive_control": positive,
        "plan": plan.read_text() if plan.is_file() else None,
    }


def run_positive_doctor(case, runtime_root, scratch):
    project = scratch / (case["id"] + "-positive")
    seed_register(project)
    (project / "AGENTS.md").write_text((BUNDLE / "cases" / (case["id"] + "-positive.md")).read_text(), encoding="utf-8")
    command = [sys.executable, "-B", str(runtime_root / "scripts/docs-doctor.py"), str(project), "--today", TODAY, "--no-git"]
    before = snapshot(project)
    output = subprocess.run(command, cwd=runtime_root, capture_output=True, text=True, timeout=15)
    return {"name": case["positive"], "project": str(project), "commands": [command],
            "before": before, "after": snapshot(project),
            "stages": [{"name": "doctor", "exit_code": output.returncode, "stdout": output.stdout, "stderr": output.stderr}],
            "exit_code": output.returncode,
            "passed": output.returncode == 0}


def run_positive_delimiter(case, runtime_root, scratch):
    kind = "cdata" if case["id"].endswith("cdata") else "pi"
    name = "contiguous-" + kind
    project = scratch / name
    seed_register(project)
    source = ROOT / "tests/fixtures/acceptance-v2" / (name + ".md")
    (project / "docs/STATUS.md").write_bytes(source.read_bytes())
    plan = project / "plan.json"
    command = [sys.executable, "-B", str(runtime_root / "scripts/docs-migrate.py"),
               str(project), "--register-dir", "docs", "--plan", str(plan), "--today", TODAY]
    before = snapshot(project)
    output = subprocess.run(command, cwd=runtime_root, capture_output=True, text=True, timeout=15)
    return {"name": name, "project": str(project), "commands": [command],
            "stages": [{"name": "preview", "exit_code": output.returncode, "stdout": output.stdout, "stderr": output.stderr}],
            "exit_code": output.returncode, "passed": output.returncode == 0,
            "plan": plan.read_text() if plan.is_file() else None,
            "before": before, "after": snapshot(project)}


def run_positive_migration(runtime_root, scratch):
    project = scratch / "migration-20-safe-write"
    seed_register(project)
    (project / "docs/STATUS.md").write_bytes((ROOT / "tests/fixtures/migration-20/STATUS.md").read_bytes())
    before = snapshot(project)
    plan = project / "plan.json"
    preview = [sys.executable, "-B", str(runtime_root / "scripts/docs-migrate.py"), str(project),
               "--register-dir", "docs", "--plan", str(plan), "--today", TODAY]
    first = subprocess.run(preview, cwd=runtime_root, capture_output=True, text=True, timeout=15)
    if first.returncode != 0 or not plan.is_file():
        raise GateError("generic migration positive preview failed")
    data = json.loads(plan.read_text())
    for mapping in data.get("mappings", []):
        if not mapping.get("existing"):
            mapping["reviewed"] = True
            mapping["row"]["closes_when"] = "Acceptance positive control is reviewed."
    plan.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    write = preview + ["--write"]
    second = subprocess.run(write, cwd=runtime_root, capture_output=True, text=True, timeout=15)
    ledger = project / "docs/LEDGER.md"
    return {"name": "migration-20-safe-write", "project": str(project), "commands": [preview, write],
            "stages": [{"name": name, "exit_code": output.returncode, "stdout": output.stdout, "stderr": output.stderr}
                       for name, output in [("preview", first), ("write", second)]],
            "exit_code": second.returncode, "passed": second.returncode == 0,
            "before": before, "after": snapshot(project), "plan": plan.read_text(),
            "ledger": ledger.read_text() if ledger.is_file() else "",
            "journal": (project / "docs/.docs-migrate-journal.json").read_text() if (project / "docs/.docs-migrate-journal.json").is_file() else ""}


def expected_cases(manifest: dict) -> dict[str, dict]:
    return {
        case["id"]: {
            "outcome": "reject" if int(case["exit"]) else "accept",
            "exit_code": int(case["exit"]),
            "assertion": case["assertion"],
        }
        for case in manifest["cases"]
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args(argv)
    args.runtime_root = args.runtime_root.resolve()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    payload = {
        "schema": 2,
        "interpreter": sys.executable,
        "evidence_scope": "core-doctor-migration",
        "successful": False,
        "exit_code": 0,
        "tests": len(manifest["cases"]),
        "failures": [],
        "errors": [],
        "skips": [],
        "expected_failures": [],
        "runtime_hashes": {},
        "source_provenance": {},
        "source_commit": args.source_commit,
        "runtime_root": str(args.runtime_root),
        "cases": [],
    }
    try:
        verify_manifest(manifest)
        payload["runtime_hashes"] = runtime_hashes(args.runtime_root)
        payload["source_provenance"] = git_provenance(args.runtime_root, args.source_commit)
        payload["source_provenance"]["runtime_tree_sha256"] = tree_hash(payload["runtime_hashes"])
        with tempfile.TemporaryDirectory(prefix="acceptance-child-") as directory:
            scratch = Path(directory)
            payload["cases"] = [run_case(case, args.runtime_root, scratch)
                                for case in manifest["cases"]]
            payload["generic_control"] = run_positive_migration(args.runtime_root, scratch)
        payload["successful"] = True
        validate_result(payload, expected_cases(manifest), payload["runtime_hashes"], strict=True)
    except (OSError, ValueError, TypeError, json.JSONDecodeError, GateError) as error:
        payload["failures"] = [{"type": type(error).__name__, "message": str(error)}]
        payload["successful"] = False
        payload["exit_code"] = 1
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    if payload["successful"] and not payload["failures"]:
        print(json.dumps({"accepted": True, "cases": len(payload["cases"])}, sort_keys=True))
        return 0
    print("REJECT: acceptance bundle failed", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
