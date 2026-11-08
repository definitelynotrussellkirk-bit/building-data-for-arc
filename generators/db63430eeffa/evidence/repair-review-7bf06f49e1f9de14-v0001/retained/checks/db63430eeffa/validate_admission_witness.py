#!/usr/bin/env python3
"""Run the packet's exact source-binding validator and protected witness replay."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from arcpuzzles.review_parametric_admission import (
    validate_ready_evidence,
    validate_sequential_witness,
)
from arcpuzzles.review_sequential_replay import replay_witness


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    repo = Path.cwd().resolve()
    work = repo.parent
    results = json.loads((work / "RESULTS.json").read_text(encoding="utf-8"))
    contract = json.loads((work / "ASSIGNMENT.json").read_text(encoding="utf-8"))
    target = next(
        row for row in results["repair_targets"] if row["task_id"] == contract["task_id"]
    )
    progress = target["parametric_work"]

    def read(name: str) -> bytes:
        return (work / name).read_bytes()

    qualification = json.loads(read(progress["qualification_path"]))
    inventory = {
        "repo/" + row["path"] for row in qualification["source_binding"]["files"]
    }
    inventory.add(progress["inventory_path"])
    reported = validate_ready_evidence(contract, progress, read, inventory)
    static = validate_sequential_witness(progress, reported, read)
    witness = json.loads(read(progress["sequential_dependency"]["witness_path"]))
    replay = replay_witness(repo, witness)
    report = {
        "schema": "arcpuzzles-review-witness-preflight-v1",
        "task_id": contract["task_id"],
        "static_validation": static,
        "protected_replay": replay,
        "limits": [
            "This preflight does not perform owner acceptance.",
            "The owner must replay against the integrated exact source before admission.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": "pass",
        "static": static["status"],
        "cases": static["cases"],
        "owner_replay": replay["status"],
        "evaluations": replay["evaluations"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
