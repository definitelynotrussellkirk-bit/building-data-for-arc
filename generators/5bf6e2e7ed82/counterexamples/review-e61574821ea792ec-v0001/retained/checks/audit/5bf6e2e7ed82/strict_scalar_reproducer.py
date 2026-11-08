#!/usr/bin/env python3
"""Read-only source-bound reproducer for the 5bf6e2e7ed82 scalar contract."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "5bf6e2e7ed82"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = find_root(__file__)
    gen, source, source_sha = load_selected_generator(TASK_ID, root=root)
    cases = [
        {"name": "fractional_exact_override", "seed": 991, "sample_index": 0,
         "difficulty": "easy", "overrides": {"target_size": 7.75}},
        {"name": "negative_sample_index", "seed": 991, "sample_index": -1,
         "difficulty": "easy", "overrides": {}},
        {"name": "boolean_seed", "seed": True, "sample_index": 0,
         "difficulty": "easy", "overrides": {}},
    ]
    results = []
    for case in cases:
        try:
            grid = gen.generate(
                case["seed"], case["sample_index"],
                difficulty=case["difficulty"], **case["overrides"]
            )
        except Exception as exc:
            result = {**case, "status": "rejected", "exception": type(exc).__name__,
                      "message": str(exc)}
        else:
            result = {
                **case,
                "status": "accepted_invalid_scalar",
                "shape": [len(grid), len(grid[0])],
                "observed_overrides": gen.observe_overrides(grid),
                "self_check_errors": gen.self_check(grid),
            }
        results.append(result)

    report = {
        "schema": "arcpuzzles-audit-strict-scalar-v1",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(root)),
        "generator_sha256": source_sha,
        "rule_hash": gen.RULE_HASH,
        "results": results,
        "verdict": "reproduced" if any(r["status"] == "accepted_invalid_scalar" for r in results) else "not_reproduced",
        "command": {
            "cwd": "packet_root",
            "argv": ["python3", "review.py", "run", "python3", "../checks/audit/5bf6e2e7ed82/strict_scalar_reproducer.py", "--out", "../checks/audit/5bf6e2e7ed82/strict_scalar_reproducer.json"],
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["verdict"] == "reproduced" else 1


if __name__ == "__main__":
    raise SystemExit(main())
