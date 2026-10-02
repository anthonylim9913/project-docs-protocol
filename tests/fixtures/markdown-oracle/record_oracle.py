"""Development-only snapshot writer; requires markdown-it-py==4.0.0.

Run from repository root using the ignored oracle venv described in README.
The normal test suite reads the result and never imports this dependency.
"""
import importlib.metadata
import argparse
import json
import hashlib
import os
from pathlib import Path
import sys

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[3]
SNAPSHOT = Path(__file__).with_name("observations.json")


def main():
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument('--snapshot', type=Path, default=SNAPSHOT)
    arguments.add_argument('--out', type=Path, default=SNAPSHOT)
    args = arguments.parse_args()
    version = importlib.metadata.version("markdown-it-py")
    if version != "4.0.0":
        raise SystemExit("Use markdown-it-py 4.0.0 for the retained oracle")
    parser = MarkdownIt("commonmark")
    frozen = json.loads(args.snapshot.read_text(encoding="utf-8"))
    observations = []
    # Inputs and expectations come from the frozen reviewed snapshot.  The
    # oracle never imports Doctor or any production test generator.
    for original in frozen["cases"]:
        case = {key: original[key] for key in ("name", "source", "live")}
        tokens = parser.parse(case["source"])
        observation = dict(case)
        wiring_spans = [token.map for token in tokens
                        if token.type == "inline" and
                        "This project uses the project-docs-protocol" in token.content]
        observation["oracle_live"] = bool(wiring_spans)
        observation["source_sha256"] = hashlib.sha256(case["source"].encode()).hexdigest()
        observation["oracle_assertion"] = {
            "token_type": "inline" if wiring_spans else "code_block_or_absent",
            "spans": wiring_spans,
            "source_bytes": len(case["source"].encode()),
        }
        observation["blocks"] = [
            {"type": token.type, "tag": token.tag, "lines": token.map,
             "content": token.content}
            for token in tokens if token.map is not None
        ]
        observations.append(observation)
    output = {"parser": f"markdown-it-py {version}; commonmark preset",
              "executable": "<python>",  # never the local interpreter path
              "cwd": "<repo>",  # never the local working directory
              "cases": observations}
    destination = args.out
    destination.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    disagreements = [case["name"] for case in observations if case["live"] != case["oracle_live"]]
    print(f"Recorded {len(observations)} cases; expectation disagreements: {disagreements}")
    return bool(disagreements)


if __name__ == "__main__":
    raise SystemExit(main())
