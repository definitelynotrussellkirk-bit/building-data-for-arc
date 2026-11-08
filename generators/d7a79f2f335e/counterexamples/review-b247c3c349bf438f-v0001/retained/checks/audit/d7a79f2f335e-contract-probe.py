#!/usr/bin/env python3
"""Source-bound audit reproducer for d7a79f2f335e's strict call contract."""
from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "d7a79f2f335e"


def main() -> int:
    root = find_root(__file__)
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    invalid_difficulty = "__invalid_difficulty__"
    result = {
        "schema": "arcpuzzles-audit-contract-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(source_path),
        "generator_sha256": source_sha256,
        "call": {
            "seed": 17,
            "sample_index": 0,
            "difficulty": invalid_difficulty,
            "overrides": {},
        },
    }
    try:
        grid = generator.generate(17, 0, difficulty=invalid_difficulty)
    except Exception as exc:
        result.update({"status": "rejected", "exception": repr(exc)})
    else:
        result.update(
            {
                "status": "accepted_invalid_scalar",
                "grid": grid,
                "self_check": generator.self_check(grid),
                "observed_overrides": generator.observe_overrides(grid),
            }
        )
    out = Path(__file__).with_suffix(".json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out)
    return 0 if result["status"] == "accepted_invalid_scalar" else 1


if __name__ == "__main__":
    raise SystemExit(main())
