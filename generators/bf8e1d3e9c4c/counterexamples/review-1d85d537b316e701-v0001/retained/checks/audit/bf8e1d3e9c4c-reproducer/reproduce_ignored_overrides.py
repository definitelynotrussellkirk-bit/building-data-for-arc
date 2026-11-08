#!/usr/bin/env python3
"""Source-bound reproducer for bf8e1d3e9c4c's ignored exact controls."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "bf8e1d3e9c4c"
EXPECTED_SOURCE_SHA256 = "d49256e611203fcd8ba77fc8dc492d981fc7f359a600d37c986ea4beef6508fa"
SEED = 2
SAMPLE_INDEX = 0
OVERRIDES = {
    "grid_h": 9,
    "grid_w": 9,
    "n_pairs": 2,
    "palette_size": 2,
    "n_distinct_colors": 2,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = find_root(__file__)
    gen, source, source_sha256 = load_selected_generator(TASK_ID, root=root)
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(
            f"source drift: expected {EXPECTED_SOURCE_SHA256}, got {source_sha256}"
        )

    grid = gen.generate(SEED, SAMPLE_INDEX, **OVERRIDES)
    counts = Counter(cell for row in grid for cell in row if cell != 0)
    observed = {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_pairs": len(counts),
        "palette_size": len(counts),
        "n_distinct_colors": len(counts),
        "nonzero_counts": {str(color): count for color, count in sorted(counts.items())},
    }
    mismatches = {
        key: {"requested": value, "observed": observed[key]}
        for key, value in OVERRIDES.items()
        if observed[key] != value
    }
    report = {
        "schema": "bf8e1d3e9c4c-ignored-overrides-reproducer/1",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(root)),
        "generator_source_sha256": source_sha256,
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "seed": SEED,
        "sample_index": SAMPLE_INDEX,
        "difficulty": None,
        "overrides": OVERRIDES,
        "observed": observed,
        "override_mismatches": mismatches,
        "self_check_errors": list(gen.self_check(grid)),
        "input_grid": grid,
        "reproduced": bool(mismatches),
        "scope_note": (
            "This is an API/control-contract defect, not a label counterexample. "
            "The returned input remains lawful under the task's current self_check."
        ),
        "command": [
            "python3", "review.py", "run", "python3",
            "../checks/audit/bf8e1d3e9c4c-reproducer/reproduce_ignored_overrides.py",
            "--out", "../checks/audit/bf8e1d3e9c4c-reproducer/report.json",
        ],
        "working_directory": "packet_root",
        "payload_working_directory": "repo",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "reproduced": report["reproduced"],
        "source_sha256": source_sha256,
        "mismatches": mismatches,
        "self_check_errors": report["self_check_errors"],
    }, indent=2, sort_keys=True))
    return 0 if report["reproduced"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
