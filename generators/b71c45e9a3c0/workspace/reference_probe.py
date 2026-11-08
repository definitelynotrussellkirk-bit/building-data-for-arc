"""Independent oracle and distribution probe for b71c45e9a3c0.

This module intentionally does not call production generator helpers when it
computes components, outputs, or observed axes.  It is supplementary authoring
and regression evidence; the canonical Racket program remains label authority.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

TASK = "b71c45e9a3c0"
HOME = Path(__file__).resolve().parents[1]
ROOT = None
for candidate in (HOME, *HOME.parents):
    if (candidate / "shared" / "runtime" / "reviewer_support.py").is_file():
        ROOT = candidate
        sys.path.insert(0, str(candidate / "shared" / "runtime"))
        break
if ROOT is None:
    # Copied task-test runtimes expose reviewer_support and puzzle_generators at root.
    ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(ROOT))

from reviewer_support import canonical_pairs as _canonical_pairs, find_root  # noqa: E402

LOW_COLORS = frozenset({1, 2, 4, 5})
HIGH_COLORS = frozenset({6, 7, 8, 9})


def load_generator(path=None):
    path = Path(path or os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_b71c45e9a3c0", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK, root=find_root(__file__))


def color3_components(grid):
    """Return sorted 4-connected color-3 components using independent code."""
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    cells.add(point)
                    stack.append(point)
        result.append(tuple(sorted(cells)))
    return tuple(sorted(result, key=lambda cells: (min(r for r, _ in cells), min(c for _, c in cells), cells)))


def bbox(component):
    return (
        min(r for r, _ in component),
        min(c for _, c in component),
        max(r for r, _ in component),
        max(c for _, c in component),
    )


def bbox_key_output(grid):
    """Independent intended rule: read (bbox_top-1,bbox_left) per object."""
    out = deepcopy(grid)
    for component in color3_components(grid):
        top, left, _, _ = bbox(component)
        color = grid[top - 1][left]
        for r, c in component:
            out[r][c] = color
    return out


def top_row_key_output(grid):
    """Plausible rival: key is above the leftmost occupied top-row cell."""
    out = deepcopy(grid)
    for component in color3_components(grid):
        top = min(r for r, _ in component)
        leftmost_top = min(c for r, c in component if r == top)
        color = grid[top - 1][leftmost_top]
        for r, c in component:
            out[r][c] = color
    return out


def one_key_output(grid):
    """Plausible rival: use the first object's key color for every object."""
    components = color3_components(grid)
    first_top, first_left, _, _ = bbox(components[0])
    color = grid[first_top - 1][first_left]
    out = deepcopy(grid)
    for component in components:
        for r, c in component:
            out[r][c] = color
    return out


def _component_stats(grid):
    stats = []
    for component in color3_components(grid):
        top, left, bottom, right = bbox(component)
        stats.append(
            {
                "cells": component,
                "height": bottom - top + 1,
                "width": right - left + 1,
                "gap_corner": (top, left) not in component,
                "key": grid[top - 1][left],
            }
        )
    return stats


def observed(grid):
    """Recover every advertised axis from pixels, independently."""
    stats = _component_stats(grid)
    keys = {item["key"] for item in stats}
    heights = [item["height"] for item in stats]
    if keys and keys <= LOW_COLORS:
        palette_kind = "low"
    elif keys and keys <= HIGH_COLORS:
        palette_kind = "high"
    else:
        palette_kind = "mixed"
    if heights and all(height <= 2 for height in heights):
        shape_profile = "compact"
    elif heights and all(height == 3 for height in heights):
        shape_profile = "extended"
    else:
        shape_profile = "mixed"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_groups": len(stats),
        "n_gap_shapes": sum(item["gap_corner"] for item in stats),
        "palette_kind": palette_kind,
        "shape_profile": shape_profile,
    }


def audit(module, count):
    report = {
        "schema": "b71c45e9a3c0-independent-probe-v1",
        "generator_version": module.VERSION,
        "bands": {},
        "canonical": [],
    }
    for pair in canonical_pairs():
        report["canonical"].append(
            {
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "self_check": module.self_check(pair["input"]),
                "oracle_match": bbox_key_output(pair["input"]) == pair["output"],
            }
        )
    for band in (None, "easy", "medium", "hard"):
        counts = Counter()
        distinct = set()
        axis_values = {name: set() for name in module.AXES}
        examples = []
        for index in range(count):
            grid = module.generate(910_000 + index, index * 13 + 5, difficulty=band)
            again = module.generate(910_000 + index, index * 13 + 5, difficulty=band)
            issues = module.self_check(grid)
            obs = observed(grid)
            counts["samples"] += 1
            counts["self_check_failures"] += bool(issues)
            counts["nondeterministic"] += grid != again
            counts["bbox_rival_disagreements"] += bbox_key_output(grid) != top_row_key_output(grid)
            counts["one_key_rival_disagreements"] += bbox_key_output(grid) != one_key_output(grid)
            counts["canonical_profile_hits"] += (
                obs["grid_h"] == 11 and obs["grid_w"] in (10, 11, 12) and obs["n_groups"] == 3
            )
            digest = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
            distinct.add(digest)
            for name, value in obs.items():
                axis_values.setdefault(name, set()).add(value)
            if len(examples) < 4:
                examples.append({"observed": obs, "grid": grid})
        counts["distinct_inputs"] = len(distinct)
        report["bands"][str(band)] = {
            "counts": dict(counts),
            "axis_values": {name: sorted(values, key=str) for name, values in axis_values.items()},
            "examples": examples,
        }
    return report


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=128)
    parser.add_argument("--generator")
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    module = load_generator(args.generator)
    report = audit(module, args.count)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
