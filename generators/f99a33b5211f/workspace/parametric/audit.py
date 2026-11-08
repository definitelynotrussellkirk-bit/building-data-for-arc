"""Bounded deterministic self-review for the local-axis family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_task_f99_axis_audit_prototype", path)
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
    observed_origins: set[tuple[int, int]] = set()
    observed_x_vectors: set[tuple[int, int]] = set()
    observed_y_vectors: set[tuple[int, int]] = set()
    observed_distractor_colors: set[int] = set()
    maximum_nonzero = 0
    maximum_components = 0

    for seed in range(seed_count):
        full_by_axis = {
            axis: module.generate(seed, {"axis": axis}, demos=6, queries=4)
            for axis in module.AXES
        }
        reference_inputs = [
            pair["input"] for pair in full_by_axis["x"]["train"] + full_by_axis["x"]["test"]
        ]
        for axis in module.AXES:
            episode = full_by_axis[axis]
            inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
            if inputs != reference_inputs:
                raise AssertionError("settings changed generated inputs")
            if module.fit_settings(episode["train"][:2]) != [{"axis": axis}]:
                raise AssertionError("two demonstrations did not identify axis")
            expected = [pair["output"] for pair in episode["train"][:2]]
            rival_sets = {
                "both_axes": [module.paint_both_axes(grid) for grid in reference_inputs[:2]],
                "origin_only": [module.paint_origin_only(grid) for grid in reference_inputs[:2]],
                "marker_cells_only": [module.paint_marker_cells_only(grid) for grid in reference_inputs[:2]],
            }
            for direction in module.CARDINAL:
                rival_sets[f"fixed_{direction}"] = [
                    module.paint_fixed_global_direction(grid, direction) for grid in reference_inputs[:2]
                ]
            for name, outputs in rival_sets.items():
                if outputs == expected:
                    raise AssertionError(f"declared shortcut survives lesson: {name}")
            for demos in range(2, 7):
                prefix = module.generate(seed, {"axis": axis}, demos=demos, queries=4)
                if prefix["train"] != episode["train"][:demos]:
                    raise AssertionError("demonstration stream depends on requested count")
            for queries in range(1, 5):
                prefix = module.generate(seed, {"axis": axis}, demos=2, queries=queries)
                if prefix["test"] != episode["test"][:queries]:
                    raise AssertionError("query stream is not prefix stable")

        for grid in reference_inputs:
            analysis = module.analyze(grid)
            x_out = module.transform(grid, {"axis": "x"})
            y_out = module.transform(grid, {"axis": "y"})
            if x_out == y_out:
                raise AssertionError("settings agree on a generated scene")
            if module.paint_both_axes(grid) in (x_out, y_out):
                raise AssertionError("paint-both-axes shortcut fits a label")
            observed_sizes.add((len(grid), len(grid[0])))
            observed_origins.add(analysis["origin"])
            observed_x_vectors.add(analysis["x_vector"])
            observed_y_vectors.add(analysis["y_vector"])
            observed_distractor_colors.update(analysis["distractor_colors"])
            maximum_nonzero = max(maximum_nonzero, analysis["nonzero_cells"])
            maximum_components = max(maximum_components, analysis["distractor_components"])
            checked_pairs += 1

        large = [grid for grid in reference_inputs[-4:] if len(grid) == 30 and len(grid[0]) == 30]
        if len(large) != 1:
            raise AssertionError("four-query bank lacks exactly one 30x30 scene")
        analysis = module.analyze(large[0])
        if (
            analysis["distractor_components"] < 20
            or analysis["distractor_cells"] < 100
            or analysis["nonzero_cells"] < 103
            or set(analysis["distractor_colors"]) != set(module.DISTRACTOR_COLORS)
        ):
            raise AssertionError("30x30 scene is not substantive")
        large_query_banks += 1

    if observed_x_vectors != set(module.CARDINAL) or observed_y_vectors != set(module.CARDINAL):
        raise AssertionError("bounded audit did not cover all local directions")
    return {
        "schema": "arcpuzzles-task-parametric-self-review-v1",
        "task_id": module.TASK_ID,
        "status": "passed",
        "seed_count": seed_count,
        "episodes": seed_count * len(module.SETTINGS),
        "generated_pairs_checked": checked_pairs,
        "large_query_banks": large_query_banks,
        "observed_sizes": [list(size) for size in sorted(observed_sizes)],
        "observed_origins": len(observed_origins),
        "observed_x_vectors": len(observed_x_vectors),
        "observed_y_vectors": len(observed_y_vectors),
        "observed_distractor_colors": len(observed_distractor_colors),
        "maximum_nonzero_cells": maximum_nonzero,
        "maximum_distractor_components": maximum_components,
        "checks": [
            "setting-independent matched inputs",
            "2..6 demonstration stream independence",
            "1..4 query prefix stability",
            "two-demo finite-setting identification",
            "x versus y output disagreement",
            "paint-both, origin-only, marker-only, and fixed-direction shortcut rejection",
            "all four x and y vector directions",
            "origin, size, object, and color spread",
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
