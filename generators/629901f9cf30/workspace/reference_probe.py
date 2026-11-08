#!/usr/bin/env python3
"""Independent Manhattan-Voronoi oracle and audit for 629901f9cf30."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any

TASK = "629901f9cf30"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator_6299", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    from reviewer_support import canonical_pairs as portable_pairs, find_root

    return portable_pairs(TASK, root=find_root(__file__), labeled_only=True)


def analyze(grid: Any) -> dict[str, Any]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected nonempty rectangular grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("expected rectangular grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be literal ARC colors 0..9")
    seeds = [(row, col, value) for row, values in enumerate(grid) for col, value in enumerate(values) if value]
    return {"grid_h": len(grid), "grid_w": width, "seeds": seeds}


def observed(grid: Any) -> dict[str, int]:
    info = analyze(grid)
    return {"grid_h": info["grid_h"], "grid_w": info["grid_w"], "n_seeds": len(info["seeds"])}


def _apply(grid: Any, *, seed_limit: int | None = None, tie_policy: str = "zero") -> list[list[int]]:
    info = analyze(grid)
    seeds = info["seeds"] if seed_limit is None else info["seeds"][:seed_limit]
    output = []
    for row in range(info["grid_h"]):
        values = []
        for col in range(info["grid_w"]):
            distances = [(abs(row - sr) + abs(col - sc), color) for sr, sc, color in seeds]
            best = min(distance for distance, _ in distances)
            colors = sorted({color for distance, color in distances if distance == best})
            values.append(colors[0] if len(colors) == 1 or tie_policy == "lowest" else 0)
        output.append(values)
    return output


def reference_output(grid: Any) -> list[list[int]]:
    return _apply(grid)


def first_three_seeds_output(grid: Any) -> list[list[int]]:
    """Canonical-fitting rival that ignores every seed after row-major seed 3."""
    return _apply(grid, seed_limit=3)


def lowest_color_on_ties_output(grid: Any) -> list[list[int]]:
    return _apply(grid, tie_policy="lowest")


def tie_cells(grid: Any) -> set[tuple[int, int]]:
    intended = reference_output(grid)
    lowest = lowest_color_on_ties_output(grid)
    return {
        (row, col)
        for row in range(len(intended))
        for col in range(len(intended[0]))
        if intended[row][col] != lowest[row][col]
    }



def schedule_rotation_audit(module) -> dict[str, Any]:
    """Exhaust one declared period and hold out every labelled pair once."""
    report: dict[str, Any] = {
        "period": module.LESSON_SCHEDULE_PERIOD,
        "examples_needed": module.EXAMPLES_NEEDED,
        "bands": {},
    }
    for band in (None, "easy", "medium", "hard"):
        checked = first_three_unwitnessed = tie_unwitnessed = hook_failures = 0
        for start in range(module.LESSON_SCHEDULE_PERIOD):
            episode = [
                module.generate(18_000, start + offset, difficulty=band)
                for offset in range(module.EXAMPLES_NEEDED + 1)
            ]
            for query_index, query_grid in enumerate(episode):
                demo_grids = [grid for index, grid in enumerate(episode) if index != query_index]
                demos = [{"input": grid, "output": reference_output(grid)} for grid in demo_grids]
                query = {"input": query_grid, "output": reference_output(query_grid)}
                checked += 1
                first_three_unwitnessed += not any(
                    first_three_seeds_output(grid) != reference_output(grid) for grid in demo_grids
                )
                tie_unwitnessed += not any(
                    lowest_color_on_ties_output(grid) != reference_output(grid) for grid in demo_grids
                )
                hook_failures += bool(module.lesson_identifiable(demos, query))
        report["bands"]["default" if band is None else band] = {
            "rotations_checked": checked,
            "first_three_unwitnessed": first_three_unwitnessed,
            "tie_policy_unwitnessed": tie_unwitnessed,
            "lesson_hook_failures": hook_failures,
        }
    return report

def audit(module, count: int) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema": "629901f9cf30-independent-audit-v2",
        "version": module.VERSION,
        "canonical": [],
        "bands": {},
        "schedule_rotations": schedule_rotation_audit(module),
    }
    for index, pair in enumerate(canonical_pairs()):
        report["canonical"].append(
            {
                "index": index,
                "self_check": module.self_check(pair["input"]),
                "oracle_matches": reference_output(pair["input"]) == pair["output"],
                "first_three_matches": first_three_seeds_output(pair["input"]) == pair["output"],
                "tie_cells": len(tie_cells(pair["input"])),
            }
        )
    for band in (None, "easy", "medium", "hard"):
        counters = Counter()
        axes = {name: set() for name in ("grid_h", "grid_w", "n_seeds")}
        hashes = set()
        for index in range(count):
            grid = module.generate(9000 + index, index, difficulty=band)
            counters["samples"] += 1
            counters["self_check_errors"] += bool(module.self_check(grid))
            counters["nondeterministic"] += grid != module.generate(9000 + index, index, difficulty=band)
            stats = observed(grid)
            for name, value in stats.items():
                axes[name].add(value)
            hashes.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            intended = reference_output(grid)
            counters["tie_witnesses"] += bool(tie_cells(grid))
            counters["first_three_disagreements"] += intended != first_three_seeds_output(grid)
            counters["tie_policy_disagreements"] += intended != lowest_color_on_ties_output(grid)
        report["bands"]["default" if band is None else band] = {
            **dict(counters),
            "distinct_inputs": len(hashes),
            "axes": {name: sorted(values) for name, values in axes.items()},
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=120)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report = audit(module, args.count)
    source = Path(args.generator or ROOT / f"generators/{TASK}/generator.py")
    report["generator_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    bad = any(
        item["self_check"] or not item["oracle_matches"] or not item["first_three_matches"] or not item["tie_cells"]
        for item in report["canonical"]
    )
    bad |= any(
        data["self_check_errors"]
        or data["nondeterministic"]
        or data["tie_witnesses"] != data["samples"]
        or data["tie_policy_disagreements"] != data["samples"]
        or not data["first_three_disagreements"]
        for data in report["bands"].values()
    )
    bad |= any(
        data["first_three_unwitnessed"]
        or data["tie_policy_unwitnessed"]
        or data["lesson_hook_failures"]
        for data in report["schedule_rotations"]["bands"].values()
    )
    return int(bad)


if __name__ == "__main__":
    raise SystemExit(main())
