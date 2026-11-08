"""Bounded deterministic self-review for the neighbor-mode family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_task_9f74_audit_prototype", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit(seed_count: int) -> dict:
    if type(seed_count) is not int or not 1 <= seed_count <= 512:
        raise ValueError("seed_count must be an exact integer in 1..512")
    module = _load()
    checked_pairs = 0
    large_query_banks = 0
    observed_sizes: set[tuple[int, int]] = set()
    observed_positions: set[tuple[int, int]] = set()
    observed_colors: set[int] = set()
    maximum_nonzero = 0

    for seed in range(seed_count):
        full_by_mode = {
            mode: module.generate(seed, {"neighbor_mode": mode}, demos=6, queries=4)
            for mode in module.MODES
        }
        reference_inputs = [
            pair["input"]
            for pair in full_by_mode["diagonal"]["train"] + full_by_mode["diagonal"]["test"]
        ]
        for mode in module.MODES:
            episode = full_by_mode[mode]
            inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
            if inputs != reference_inputs:
                raise AssertionError("settings changed generated inputs")
            if module.fit_settings(episode["train"][:2]) != [{"neighbor_mode": mode}]:
                raise AssertionError("two demonstrations did not identify neighbor_mode")
            for demos in range(2, 7):
                prefix = module.generate(seed, {"neighbor_mode": mode}, demos=demos, queries=4)
                if prefix["train"] != episode["train"][:demos]:
                    raise AssertionError("demonstration stream depends on requested count")
            for queries in range(1, 5):
                prefix = module.generate(seed, {"neighbor_mode": mode}, demos=2, queries=queries)
                if prefix["test"] != episode["test"][:queries]:
                    raise AssertionError("query stream is not prefix stable")

        # Inputs are setting-independent, so inspect each scene once.
        for grid in reference_inputs:
            analysis = module.analyze(grid)
            if len(analysis["diagonal"]) < 2 or len(analysis["orthogonal"]) < 2:
                raise AssertionError("scene lacks both relation classes")
            if analysis["negative_controls"] < 2:
                raise AssertionError("scene lacks controlled near-misses")
            diagonal = module.transform(grid, {"neighbor_mode": "diagonal"})
            orthogonal = module.transform(grid, {"neighbor_mode": "orthogonal"})
            if diagonal == orthogonal:
                raise AssertionError("settings agree on a generated scene")
            if module.fill_every_relation(grid) in (diagonal, orthogonal):
                raise AssertionError("fill-every-relation shortcut fits a label")
            observed_sizes.add((len(grid), len(grid[0])))
            for r, c, color in analysis["diagonal"] + analysis["orthogonal"]:
                observed_positions.add((r, c))
                observed_colors.add(color)
            maximum_nonzero = max(maximum_nonzero, sum(cell != 0 for row in grid for cell in row))
            checked_pairs += 1

        large = [grid for grid in reference_inputs[-4:] if len(grid) == 30 and len(grid[0]) == 30]
        if len(large) != 1:
            raise AssertionError("four-query bank lacks exactly one 30x30 scene")
        analysis = module.analyze(large[0])
        if (
            len(analysis["diagonal"]) < 8
            or len(analysis["orthogonal"]) < 8
            or sum(cell != 0 for row in large[0] for cell in row) < 80
        ):
            raise AssertionError("30x30 scene is not substantive")
        large_query_banks += 1

    return {
        "schema": "arcpuzzles-task-parametric-self-review-v1",
        "task_id": module.TASK_ID,
        "status": "passed",
        "seed_count": seed_count,
        "episodes": seed_count * len(module.SETTINGS),
        "generated_pairs_checked": checked_pairs,
        "large_query_banks": large_query_banks,
        "observed_sizes": [list(size) for size in sorted(observed_sizes)],
        "observed_center_positions": len(observed_positions),
        "observed_positive_colors": len(observed_colors),
        "maximum_nonzero_cells": maximum_nonzero,
        "checks": [
            "setting-independent matched inputs",
            "2..6 demonstration stream independence",
            "1..4 query prefix stability",
            "two-demo finite-setting identification",
            "both relation classes in every scene",
            "controlled partial/mismatched near-misses",
            "diagonal versus orthogonal disagreement",
            "fill-every-relation shortcut rejection",
            "position and color spread",
            "one substantive 30x30 scene in every four-query bank",
        ],
        "limits": "Finite deterministic audit; it does not prove uniqueness against all conceivable rules.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "pairs": result["generated_pairs_checked"], "out": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
