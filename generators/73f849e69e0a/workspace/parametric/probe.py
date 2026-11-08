#!/usr/bin/env python3
"""Replay the full protected-Racket qualification matrix for 73f849e69e0a."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import find_root

TASK_ID = "73f849e69e0a"
HERE = Path(__file__).resolve().parent


def qualification_jobs() -> list[dict[str, Any]]:
    return [
        {"seed": seed, "settings": {"orientation": orientation}, "demos": 3, "queries": 4}
        for orientation in ("identity", "rotate_cw")
        for seed in (0, 17)
    ]


def run() -> dict[str, Any]:
    from arcpuzzles.parametric_worker import evaluate_contract

    root = find_root(__file__)
    contract_path = HERE / "promotion.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    result = evaluate_contract(root, TASK_ID, contract, qualification_jobs())
    episodes = []
    for episode in result["episodes"]:
        episodes.append({
            "seed": episode["seed"],
            "settings": episode["settings"],
            "program_sha256": episode["program_sha256"],
            "demo_shapes": [[len(p["input"]), len(p["input"][0])] for p in episode["train"]],
            "query_input_shapes": [[len(p["input"]), len(p["input"][0])] for p in episode["test"]],
            "query_output_shapes": [[len(p["output"]), len(p["output"][0])] for p in episode["test"]],
            "input_sha256": [
                hashlib.sha256(json.dumps(p["input"], separators=(",", ":")).encode()).hexdigest()
                for p in episode["train"] + episode["test"]
            ],
        })
    return {
        "schema": "arcpuzzles-task-local-parametric-probe-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "jobs": qualification_jobs(),
        "checks": result["checks"],
        "racket": result["racket"],
        "racket_evaluations": result["racket_evaluations"],
        "episodes": episodes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(args.out)
    report = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "task_id": TASK_ID,
        "jobs": len(report["jobs"]),
        "racket_evaluations": report["racket_evaluations"],
        "protected_racket": report["racket"].get("protected"),
        "out": str(args.out.resolve()),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
