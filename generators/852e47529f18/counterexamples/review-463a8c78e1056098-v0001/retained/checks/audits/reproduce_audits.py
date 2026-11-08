#!/usr/bin/env python3
"""Reproduce the two adversarial audit findings without private runner imports."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nonzero_colors_in_column(grid: list[list[int]], col: int) -> set[int]:
    return {row[col] for row in grid if row[col] != 0}


def main() -> int:
    g852, p852 = load_generator("852e47529f18")
    only_horizontal = g852.generate(0, 0, texture="only_horizontal")
    no_six = g852.generate(0, 0, texture="no_color_6")

    g1d, p1d = load_generator("1d14de95c43e")
    bands: tuple[str | None, ...] = (None, "easy", "medium", "hard")
    grids = []
    multi_color_columns = []
    empty_columns = 0
    total_columns = 0
    for seed in range(25):
        for sample_index in range(4):
            for difficulty in bands:
                grid = g1d.generate(seed, sample_index, difficulty=difficulty)
                grids.append(grid)
                for col in range(len(grid[0])):
                    colors = nonzero_colors_in_column(grid, col)
                    total_columns += 1
                    if not colors:
                        empty_columns += 1
                    if len(colors) > 1:
                        multi_color_columns.append(
                            {
                                "seed": seed,
                                "sample_index": sample_index,
                                "difficulty": difficulty,
                                "column": col,
                                "colors": sorted(colors),
                            }
                        )

    majority_counterexample = [[4], [6], [6], [0]]
    result: dict[str, Any] = {
        "schema": "arcpuzzles-review-audit-reproduction-v1",
        "cwd": os.fspath(ROOT),
        "852e47529f18": {
            "generator_sha256": sha256(p852),
            "only_horizontal_matches_saved_input": only_horizontal
            == json.loads((ROOT / "checks/audit/852e47529f18/input.json").read_text()),
            "only_horizontal_self_check": g852.self_check(only_horizontal),
            "only_horizontal_self_check_with_meta": g852.self_check(
                only_horizontal, meta={"texture": "only_horizontal"}
            ),
            "no_color_6_self_check": g852.self_check(no_six),
            "no_color_6_self_check_with_meta": g852.self_check(
                no_six, meta={"texture": "no_color_6"}
            ),
        },
        "1d14de95c43e": {
            "generator_sha256": sha256(p1d),
            "survey": {
                "seeds": [0, 24],
                "sample_indices": [0, 3],
                "difficulties": [None, "easy", "medium", "hard"],
                "grids": len(grids),
                "total_columns": total_columns,
                "empty_columns": empty_columns,
                "multi_color_columns": len(multi_color_columns),
                "first_multi_color_columns": multi_color_columns[:10],
            },
            "majority_counterexample_self_check": g1d.self_check(majority_counterexample),
        },
    }
    out = ROOT / "checks/audits/reproduction.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
