#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "2786bc764238"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = Path.cwd()
    gen, source_path, source_sha = load_selected_generator(TASK_ID, root=root)

    cases = []
    for difficulty in ("easy", None, "hard"):
        grid = gen.generate(991, 0, difficulty=difficulty, largest_size=11.0)
        cases.append({
            "call": {
                "seed": 991,
                "sample_index": 0,
                "difficulty": difficulty,
                "largest_size": 11.0,
                "largest_size_type": "float",
            },
            "accepted": True,
            "observed": gen.observe_overrides(grid),
            "self_check": gen.self_check(grid, difficulty=difficulty),
            "grid": grid,
        })
    negative_index = gen.generate(991, -1, difficulty="easy")
    result = {
        "schema": "arcpuzzles-audit-strict-scalar-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(source_path.relative_to(root)),
        "generator_sha256": source_sha,
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "finding": "declared integer override and nonnegative index contract accept coercible/negative scalars",
        "float_override_cases": cases,
        "negative_sample_index": {
            "call": {"seed": 991, "sample_index": -1, "difficulty": "easy"},
            "accepted": True,
            "self_check": gen.self_check(negative_index, difficulty="easy"),
            "grid": negative_index,
        },
        "expected_contract": {
            "AXES.largest_size.type": gen.AXES["largest_size"]["type"],
            "sample_index": "literal nonnegative Python integer",
        },
        "reproduced": all(not row["self_check"] for row in cases),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"reproduced": result["reproduced"], "generator_sha256": source_sha}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
