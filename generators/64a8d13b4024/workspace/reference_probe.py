#!/usr/bin/env python3
"""Independent oracle and audit probe for ARC task 64a8d13b4024.

The probe deliberately does not import parsing or rule helpers from the generator.
It can audit the in-tree generator or an alternate generator.py via --generator.
"""
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

TASK = "64a8d13b4024"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator_64a", source)
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
    if any(type(value) is not int or value not in (0, 1, 2, 3) for row in grid for value in row):
        raise ValueError("cells must be literal integers in {0,1,2,3}")
    counts = tuple(sum(value == color for row in grid for value in row) for color in (1, 2, 3))
    return {"grid_h": len(grid), "grid_w": width, "counts": counts}


def observed(grid: Any) -> dict[str, int]:
    info = analyze(grid)
    n1, n2, n3 = info["counts"]
    return {
        "grid_h": info["grid_h"],
        "grid_w": info["grid_w"],
        "n1": n1,
        "n2": n2,
        "n3": n3,
    }


def reference_output(grid: Any) -> list[list[int]]:
    n1, n2, n3 = analyze(grid)["counts"]
    counts = (n1, n2, n3)
    return [
        [color if row >= 6 - counts[color - 1] else 0 for color in (1, 2, 3)]
        for row in range(6)
    ]


def capped_five_output(grid: Any) -> list[list[int]]:
    """Canonical-fitting rival: silently cap every bar height at five."""
    counts = tuple(min(5, count) for count in analyze(grid)["counts"])
    return [
        [color if row >= 6 - counts[color - 1] else 0 for color in (1, 2, 3)]
        for row in range(6)
    ]



def schedule_rotation_audit(module) -> dict[str, Any]:
    """Exhaust one declared period and hold out every labelled pair once."""
    report: dict[str, Any] = {
        "period": module.LESSON_SCHEDULE_PERIOD,
        "examples_needed": module.EXAMPLES_NEEDED,
        "bands": {},
    }
    for band in (None, "easy", "medium", "hard"):
        checked = unwitnessed = hook_failures = 0
        for start in range(module.LESSON_SCHEDULE_PERIOD):
            episode = [
                module.generate(17_000, start + offset, difficulty=band)
                for offset in range(module.EXAMPLES_NEEDED + 1)
            ]
            for query_index, query_grid in enumerate(episode):
                demo_grids = [grid for index, grid in enumerate(episode) if index != query_index]
                demos = [{"input": grid, "output": reference_output(grid)} for grid in demo_grids]
                query = {"input": query_grid, "output": reference_output(query_grid)}
                checked += 1
                unwitnessed += not any(
                    capped_five_output(grid) != reference_output(grid) for grid in demo_grids
                )
                hook_failures += bool(module.lesson_identifiable(demos, query))
        report["bands"]["default" if band is None else band] = {
            "rotations_checked": checked,
            "unwitnessed_rotations": unwitnessed,
            "lesson_hook_failures": hook_failures,
        }
    return report

def audit(module, count: int) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema": "64a8d13b4024-independent-audit-v2",
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
                "rival_matches": capped_five_output(pair["input"]) == pair["output"],
            }
        )
    for band in (None, "easy", "medium", "hard"):
        counters = Counter()
        axes = {name: set() for name in ("grid_h", "grid_w", "n1", "n2", "n3")}
        hashes = set()
        for index in range(count):
            grid = module.generate(7000 + index, index, difficulty=band)
            counters["samples"] += 1
            counters["self_check_errors"] += bool(module.self_check(grid))
            counters["nondeterministic"] += grid != module.generate(7000 + index, index, difficulty=band)
            stats = observed(grid)
            for name, value in stats.items():
                axes[name].add(value)
            hashes.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            intended = reference_output(grid)
            counters["changed"] += intended != grid
            counters["cap_five_disagreements"] += intended != capped_five_output(grid)
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
        item["self_check"] or not item["oracle_matches"] or not item["rival_matches"]
        for item in report["canonical"]
    )
    bad |= any(
        data["self_check_errors"] or data["nondeterministic"] or not data["cap_five_disagreements"]
        for data in report["bands"].values()
    )
    bad |= any(
        data["unwitnessed_rotations"] or data["lesson_hook_failures"]
        for data in report["schedule_rotations"]["bands"].values()
    )
    return int(bad)


if __name__ == "__main__":
    raise SystemExit(main())
