"""Read-only geometry probe; no labels or reference outputs are generated.

Run with the library/runtime import paths and optionally ``--out RESULT.json``.
The broad probe calls the construction helper but checks its returned points
independently. Boundary cases exercise the public generator and inspect grids.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
from pathlib import Path

from reviewer_support import find_root


TASK = "f68fe53c1702"
BBOX_RANGE = range(3, 25)
RICH_COUNTS = range(4, 8)
HELPER_SEEDS = range(4)
BOUNDARY_CANVASES = ((4, 5), (4, 24), (24, 5), (24, 24))
BOUNDARY_COUNTS = range(2, 8)
BOUNDARY_INDICES = range(3)


def inspect_points(points, height, width, count, *, rich):
    """Check count, bounds and witnesses without generator analysis helpers."""
    assert len(points) == count, "returned marker count differs from request"
    assert len(set(points)) == count, "duplicate coordinates reduce marker count"
    assert all(type(r) is int and type(c) is int
               and 0 <= r < height and 0 <= c < width for r, c in points), "invalid coordinate"
    top = min(r for r, _ in points)
    bottom = max(r for r, _ in points)
    left = min(c for _, c in points)
    right = max(c for _, c in points)
    assert bottom - top >= 2 and right - left >= 2, "bbox span below 3x3"
    if rich:
        assert (top, left, bottom, right) == (0, 0, height - 1, width - 1), "rich extrema lost"
        occupied = set(points)
        assert not ((top, left) in occupied and (bottom, right) in occupied), "occupied NW/SE pair"
        assert not ((top, right) in occupied and (bottom, left) in occupied), "occupied NE/SW pair"
        assert any(top < r < bottom and left < c < right for r, c in points), "no strict interior marker"


def probe():
    root = find_root(__file__)
    candidates = (root / "generators" / TASK / "generator.py",
                  root / "puzzle_generators" / "per_puzzle" / TASK / "generator.py")
    source = next((p for p in candidates if p.is_file()), None)
    if source is None:
        raise FileNotFoundError(f"No generator found in {candidates}")
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location("bbox_geometry_probe_generator", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    helper_cases = 0
    for height in BBOX_RANGE:
        for width in BBOX_RANGE:
            for count in RICH_COUNTS:
                if height * width - 4 < count:
                    continue
                for seed in HELPER_SEEDS:
                    try:
                        points = module._rich_markers(random.Random(seed), height, width, count)
                        inspect_points(points, height, width, count, rich=True)
                    except Exception as exc:
                        raise AssertionError(f"rich helper h={height}, w={width}, count={count}, seed={seed}: {exc}") from exc
                    helper_cases += 1

    feasible_cases = boundary_cases = 0
    for height, width in BOUNDARY_CANVASES:
        for count in BOUNDARY_COUNTS:
            for rich in (False, True):
                if rich and count < 4:
                    continue
                assert module._feasible_spans(height, width, count, rich), (
                    "no feasible spans", height, width, count, rich)
                feasible_cases += 1
            for index in BOUNDARY_INDICES:
                grid = module.generate(0, index, difficulty="hard", grid_h=height,
                                       grid_w=width, color=9, num_cells=count)
                assert len(grid) == height and all(len(row) == width for row in grid), "wrong canvas size"
                assert all(type(value) is int and value in (0, 9) for row in grid for value in row), "wrong color/type"
                points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
                inspect_points(points, height, width, count, rich=False)
                boundary_cases += 1

    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash, "generator source changed during probe"
    return {
        "status": "PASS", "task_id": TASK, "root": str(root),
        "generator_source": str(source), "generator_sha256": source_hash,
        "probe_source": str(Path(__file__).resolve()),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "rich_helper": {
            "bbox_height_inclusive": [3, 24], "bbox_width_inclusive": [3, 24],
            "counts": list(RICH_COUNTS), "seeds": list(HELPER_SEEDS),
            "eligibility": "height * width - 4 >= count", "cases": helper_cases,
            "invariants": ["exact distinct count", "integer coordinates within bbox",
                           "full intended bbox", "no occupied opposite-corner pair",
                           "strictly interior marker"],
        },
        "boundary_feasibility": {
            "canvases": [list(shape) for shape in BOUNDARY_CANVASES],
            "counts": list(BOUNDARY_COUNTS), "rich_min_count": 4,
            "cases": feasible_cases, "invariants": ["nonempty feasible spans"],
        },
        "public_boundary_generation": {
            "canvases": [list(shape) for shape in BOUNDARY_CANVASES],
            "counts": list(BOUNDARY_COUNTS), "seed": 0,
            "indices": list(BOUNDARY_INDICES), "difficulty": "hard", "color": 9,
            "cases": boundary_cases,
            "invariants": ["exact canvas", "exact distinct marker count",
                           "requested color with zero background", "bbox span at least 3x3"],
        },
        "scope": "Geometry and feasibility only; no reference labels or golden outputs computed. Finite seed coverage, exhaustive declared bbox dimensions/counts for the rich helper.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = probe()
    output = json.dumps(result, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
