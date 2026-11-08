#!/usr/bin/env python3
"""Minimal source-bound override witness for 635001043e0f."""
from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
TASK = "635001043e0f"
GEN_PATH = REPO / "generators" / TASK / "generator.py"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_sha(grid) -> str:
    return sha(json.dumps(grid, separators=(",", ":")).encode())


def describe(module, grid):
    directions = []
    for _, cells in module._nonzero_components(grid):
        directions.extend(module._tab_direction(cells))
    return {
        "grid_sha256": grid_sha(grid),
        "shape": [len(grid), len(grid[0])],
        "object_count": len(module._nonzero_components(grid)),
        "directions": directions,
        "self_check": module.self_check(grid, difficulty="easy"),
    }


def main():
    module = importlib.import_module(f"generators.{TASK}.generator")
    seed, sample_index, difficulty = 0, 1, "easy"
    cases = [
        ("default", {}),
        ("direction_up", {"direction": "up"}),
        ("direction_down", {"direction": "down"}),
        ("direction_left", {"direction": "left"}),
        ("direction_right", {"direction": "right"}),
        ("n_objects_1", {"n_objects": 1}),
        ("n_objects_2", {"n_objects": 2}),
        ("n_objects_3", {"n_objects": 3}),
        ("n_objects_4", {"n_objects": 4}),
        ("unknown_axis", {"__override_contract_unknown_axis__": 123}),
    ]
    results = []
    for label, overrides in cases:
        try:
            grid = module.generate(seed, sample_index, difficulty=difficulty, **overrides)
            results.append({"label": label, "overrides": overrides, "accepted": True, **describe(module, grid)})
        except Exception as exc:
            results.append({"label": label, "overrides": overrides, "accepted": False, "error": repr(exc)})

    default_hash = results[0]["grid_sha256"]
    report = {
        "schema": "arc-review-audit-override-witness-v1",
        "task_id": TASK,
        "generator_sha256": sha(GEN_PATH.read_bytes()),
        "generate_call": {"seed": seed, "sample_index": sample_index, "difficulty": difficulty},
        "declared_axes": module.AXES,
        "results": results,
        "all_accepted_outputs_identical_to_default": all(
            row.get("accepted") and row.get("grid_sha256") == default_hash for row in results
        ),
        "contradictory_direction_overrides_realized_directions": {
            row["label"]: row.get("directions") for row in results if row["label"].startswith("direction_")
        },
        "contradictory_object_count_overrides_realized_counts": {
            row["label"]: row.get("object_count") for row in results if row["label"].startswith("n_objects_")
        },
        "conclusion": (
            "Declared exact controls direction and n_objects are silently ignored, and an unknown key is accepted. "
            "At the retained call, every contradictory override returns the exact default bytes."
        ),
    }
    out = Path(__file__).with_name("override_witness.json")
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "out": str(out),
        "generator_sha256": report["generator_sha256"],
        "all_identical": report["all_accepted_outputs_identical_to_default"],
        "directions": report["contradictory_direction_overrides_realized_directions"],
        "counts": report["contradictory_object_count_overrides_realized_counts"],
        "unknown_axis_accepted": next(r["accepted"] for r in results if r["label"] == "unknown_axis"),
    }, indent=2))


if __name__ == "__main__":
    main()
