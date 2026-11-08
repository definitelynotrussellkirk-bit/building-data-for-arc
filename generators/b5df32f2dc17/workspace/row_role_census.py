#!/usr/bin/env python3
"""Task-local census for row-role and shortcut coverage in b5df32f2dc17.

Run from any directory.  A generator path may point at the selected source or a
retained baseline copy; canonical statistics always come from reviewer_support.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ID = "b5df32f2dc17"
REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def load_generator(path: Path):
    spec = importlib.util.spec_from_file_location(f"row_role_census_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row_runs(row: list[int]) -> list[tuple[int, int, int]]:
    runs = []
    column = 0
    while column < len(row):
        if row[column] == 0:
            column += 1
            continue
        start = column
        color = row[column]
        while column + 1 < len(row) and row[column + 1] == color:
            column += 1
        runs.append((start, column - start + 1, color))
        column += 1
    return runs


def row_role(row: list[int]) -> str:
    runs = row_runs(row)
    lengths = [length for _, length, _ in runs]
    if not runs:
        return "blank"
    if len(runs) == 1:
        return "single"
    if lengths == sorted(lengths, reverse=True):
        return "multi_already_sorted"
    return "multi_needs_reorder"


def color_order(row: list[int]) -> str:
    colors = [color for _, _, color in row_runs(row)]
    if len(colors) < 2:
        return "na"
    if colors == sorted(colors):
        return "ascending"
    if colors == sorted(colors, reverse=True):
        return "descending"
    return "mixed"


def empty_stats() -> dict[str, Counter]:
    return {
        "row_roles": Counter(),
        "row_run_counts": Counter(),
        "length_order_templates": Counter(),
        "row_color_orders": Counter(),
        "role_signatures": Counter(),
        "scene_flags": Counter(),
    }


def add_scene(stats: dict[str, Counter], grid: list[list[int]]) -> None:
    roles = [row_role(row) for row in grid]
    run_lists = [row_runs(row) for row in grid]
    stats["role_signatures"]["|".join(roles)] += 1
    for role, runs, row in zip(roles, run_lists, grid):
        stats["row_roles"][role] += 1
        stats["row_run_counts"][str(len(runs))] += 1
        stats["row_color_orders"][color_order(row)] += 1
        if runs:
            stats["length_order_templates"][",".join(str(run[1]) for run in runs)] += 1

    multi_color_orders = [
        color_order(row) for row, runs in zip(grid, run_lists) if len(runs) >= 2
    ]
    flags = {
        "has_blank": "blank" in roles,
        "has_single": "single" in roles,
        "has_already_sorted": "multi_already_sorted" in roles,
        "has_reorder": "multi_needs_reorder" in roles,
        "mixed_roles": len(set(roles)) > 1,
        "all_rows_reorder": all(role == "multi_needs_reorder" for role in roles),
        "all_rows_same_run_count": len({len(runs) for runs in run_lists}) == 1,
        "all_multirun_colors_ascending": bool(multi_color_orders)
        and all(order == "ascending" for order in multi_color_orders),
    }
    for name, value in flags.items():
        stats["scene_flags"][name] += int(value)


def json_stats(stats: dict[str, Counter]) -> dict[str, dict[str, int]]:
    return {
        name: dict(sorted(counter.items(), key=lambda item: item[0]))
        for name, counter in stats.items()
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--draws-per-band", type=int, default=200)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    generator_path = args.generator.resolve()
    generator = load_generator(generator_path)
    report: dict[str, Any] = {
        "schema": f"{TASK_ID}-row-role-census-v2",
        "generator_path": str(generator_path),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "draws_per_band": args.draws_per_band,
        "sampling": {
            "difficulties": ["easy", "medium", "hard"],
            "seed_formula": "820000 + 10000*band_index + draw_index",
            "sample_index_formula": "draw_index",
        },
        "bands": {},
    }

    for band_index, difficulty in enumerate(("easy", "medium", "hard")):
        stats = empty_stats()
        errors = []
        for index in range(args.draws_per_band):
            seed = 820_000 + 10_000 * band_index + index
            grid = generator.generate(seed, index, difficulty=difficulty)
            check_errors = generator.self_check(grid)
            if check_errors:
                errors.append({"seed": seed, "sample_index": index, "errors": check_errors})
            add_scene(stats, grid)
        report["bands"][difficulty] = {
            **json_stats(stats),
            "self_check_failures": errors,
        }

    canonical = empty_stats()
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    for pair in pairs:
        add_scene(canonical, pair["input"])
    report["canonical"] = {**json_stats(canonical), "scenes": len(pairs)}

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
