#!/usr/bin/env python3
"""Reproduce the two audit-only dead-control findings without editing targets."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1] / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
sys.path.insert(0, str(REPO / "src"))

CONFIGS = {
    "fa2e57ec3fa2": {
        "pairs": {
            "palette_kind": ["no_walls", "many_walls"],
            "wall_colors": ["1", "9"],
            "palette_size": [2, 8],
            "n_distinct_colors": [2, 8],
        },
        "exact": ["palette_kind", "no_walls", "many_walls", 123, 7, "medium"],
    },
    "4e9b5d003ae7": {
        "pairs": {
            "anchor_corner": [False, True],
            "asymmetry_force": [False, True],
            "include_decoy": [False, True],
        },
        "exact": ["include_decoy", False, True, 123, 7, "medium"],
    },
}


def load(task_id: str):
    source = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def grid_hash(grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def run(task_id: str, config: dict) -> dict:
    module, source = load(task_id)
    paired = {}
    for axis, values in config["pairs"].items():
        same = valid = 0
        first_hashes = set()
        for band in ("easy", "medium", "hard"):
            for index in range(40):
                seed = 10_000 + index
                first = module.generate(seed, index, difficulty=band, **{axis: values[0]})
                second = module.generate(seed, index, difficulty=band, **{axis: values[1]})
                same += first == second
                valid += not module.self_check(first)
                valid += not module.self_check(second)
                first_hashes.add(grid_hash(first))
        paired[axis] = {
            "values": values,
            "identical_pairs": same,
            "pairs": 120,
            "valid_outputs": valid,
            "generated_grids": 240,
            "distinct_first_variant_inputs": len(first_hashes),
        }

    try:
        unknown = module.generate(77, 5, difficulty="medium", definitely_unknown_axis=123)
        unknown_result = {"accepted": True, "self_check": module.self_check(unknown)}
    except Exception as exc:  # pragma: no cover - evidence should preserve any future rejection
        unknown_result = {"accepted": False, "exception": f"{type(exc).__name__}: {exc}"}

    axis, first_value, second_value, seed, index, band = config["exact"]
    first = module.generate(seed, index, difficulty=band, **{axis: first_value})
    second = module.generate(seed, index, difficulty=band, **{axis: second_value})
    report = {
        "schema": "arcpuzzles-audit-control-probe-v1",
        "task_id": task_id,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "sample_range": {
            "seed_formula": "10000+i",
            "sample_index": "i",
            "i": "0..39",
            "bands": ["easy", "medium", "hard"],
        },
        "paired_axes": paired,
        "unknown_override": unknown_result,
        "exact_pair": {
            "seed": seed,
            "sample_index": index,
            "difficulty": band,
            "axis": axis,
            "first_value": first_value,
            "second_value": second_value,
            "byte_identical": first == second,
            "first_grid_sha256": grid_hash(first),
            "second_grid_sha256": grid_hash(second),
            "first_self_check": module.self_check(first),
            "second_self_check": module.self_check(second),
            "first_grid": first,
            "second_grid": second,
        },
    }
    return report


def main() -> int:
    bad = False
    for task_id, config in CONFIGS.items():
        report = run(task_id, config)
        destination = HERE / task_id / "control-probe-replay.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        expected = report["paired_axes"]
        bad |= any(row["identical_pairs"] != row["pairs"] for row in expected.values())
        bad |= not report["unknown_override"].get("accepted")
        print(task_id, destination, {k: v["identical_pairs"] for k, v in expected.items()})
    return int(bad)


if __name__ == "__main__":
    raise SystemExit(main())
