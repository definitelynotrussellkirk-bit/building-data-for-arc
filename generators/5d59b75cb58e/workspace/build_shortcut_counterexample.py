"""Materialize a generated witness against the canonical lower-only shortcut."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator


TASK_ID = "5d59b75cb58e"
SEED = 90210
SAMPLE_INDEX = 1
DIFFICULTY = "medium"
OVERRIDES = {
    "side": 8,
    "n_blobs": 2,
    "blob_size": 3,
    "source_sides": "upper",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    root = find_root(__file__)
    gen, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    grid = gen.generate(
        SEED,
        SAMPLE_INDEX,
        difficulty=DIFFICULTY,
        **OVERRIDES,
    )
    official_mirror = gen.rule_mirror(grid)
    rival = gen.CANONICAL_SHORTCUTS["lower_only_add"](grid)
    if official_mirror == rival:
        raise AssertionError("chosen generated witness does not distinguish lower_only_add")
    errors = gen.self_check(grid)
    if errors:
        raise AssertionError(f"generated witness failed self_check: {errors}")

    differing = [
        {"row": r, "column": c, "intended": official_mirror[r][c], "rival": rival[r][c]}
        for r in range(len(grid))
        for c in range(len(grid[r]))
        if official_mirror[r][c] != rival[r][c]
    ]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
    (args.out_dir / "rival.json").write_text(json.dumps(rival, indent=2) + "\n")
    report = {
        "schema": "generator-shortcut-witness-v1",
        "task_id": TASK_ID,
        "generator_path": str(source_path.relative_to(root)),
        "generator_sha256": source_sha256,
        "rule_hash": gen.RULE_HASH,
        "seed": SEED,
        "sample_index": SAMPLE_INDEX,
        "difficulty": DIFFICULTY,
        "overrides": OVERRIDES,
        "observed_axes": gen.observe_overrides(grid),
        "self_check_errors": errors,
        "rival": "CANONICAL_SHORTCUTS.lower_only_add",
        "differing_cells": differing,
        "rival_output_path": "rival.json",
        "input_path": "input.json",
        "official_output": "obtain independently with arcpuzzles apply",
    }
    (args.out_dir / "witness.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
