"""Current-source reproduction of the convexify-before-extents shortcut."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "48bda9528e71"
ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / "repo"
GEN_PATH = REPO / "generators" / TASK / "generator.py"
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def load():
    spec = importlib.util.spec_from_file_location("audit_48", GEN_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def convex_hull(points):
    pts = sorted(set(points))
    if len(pts) <= 1:
        return pts
    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def inside_convex(p, hull):
    if len(hull) < 3:
        return p in hull
    signs = [cross(hull[i], hull[(i + 1) % len(hull)], p) for i in range(len(hull))]
    return all(value >= 0 for value in signs) or all(value <= 0 for value in signs)


def convexify(cells, height, width):
    hull = convex_hull(cells)
    return {
        (r, c)
        for r in range(height)
        for c in range(width)
        if inside_convex((r, c), hull)
    }


def extent_positions(cells, height, width):
    positions = set()
    for row in {r for r, _ in cells}:
        cols = [c for r, c in cells if r == row]
        if min(cols) > 0:
            positions.add((row, min(cols) - 1))
        if max(cols) + 1 < width:
            positions.add((row, max(cols) + 1))
    for col in {c for _, c in cells}:
        rows = [r for r, c in cells if c == col]
        if min(rows) > 0:
            positions.add((min(rows) - 1, col))
        if max(rows) + 1 < height:
            positions.add((max(rows) + 1, col))
    return positions


def rival(grid):
    height, width = len(grid), len(grid[0])
    occupied = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 8}
    counts = Counter(v for row in grid for v in row if v != 8)
    rare = min((count, color) for color, count in counts.items())[1]
    filled = convexify(occupied, height, width)
    output = [[8] * width for _ in range(height)]
    for r, c in extent_positions(filled, height, width):
        output[r][c] = rare
    return output, filled


def witness():
    grid = [[8] * 9 for _ in range(9)]
    occupied = (
        {(r, c) for r in range(2, 5) for c in range(2, 7)}
        | {(r, c) for r in range(5, 7) for c in range(2, 5)}
    )
    for r, c in occupied:
        grid[r][c] = 4
    grid[3][3] = 2
    return grid


def diffs(a, b):
    return [
        [r, c, a[r][c], b[r][c]]
        for r in range(len(a))
        for c in range(len(a[0]))
        if a[r][c] != b[r][c]
    ]


def main():
    module = load()
    grid = witness()
    assert module.self_check(grid) == []
    true = module.rule_mirror(grid)
    guessed, filled = rival(grid)
    witness_record = {
        "input": grid,
        "true_output": true,
        "rival_output": guessed,
        "added_by_convexification": sorted([list(p) for p in filled - {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v != 8}]),
        "differences": diffs(true, guessed),
    }
    if witness_record["differences"] != [[5, 5, 2, 8]]:
        raise AssertionError(witness_record["differences"])

    bands = {}
    aggregate = Counter()
    for band in ("easy", "medium", "hard"):
        counts = Counter()
        for i in range(100):
            grid_i = module.generate(
                5000 + i,
                i * 19 + 7,
                difficulty=band,
                scene_profile="general",
            )
            true_i = module.rule_mirror(grid_i)
            rival_i, filled_i = rival(grid_i)
            occupied_i = {(r, c) for r, row in enumerate(grid_i) for c, v in enumerate(row) if v != 8}
            counts["samples"] += 1
            counts["accepted"] += module.self_check(grid_i) == []
            counts["rival_matches"] += rival_i == true_i
            counts["convexification_changes_mask"] += filled_i != occupied_i
        bands[band] = dict(counts)
        aggregate.update(counts)

    summary = {
        "schema": "48bda9528e71-convexify-shortcut-current-source-v1",
        "task": TASK,
        "generator_version": module.VERSION,
        "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
        "witness": {
            "self_check": module.self_check(witness()),
            "differences": witness_record["differences"],
            "added_by_convexification": witness_record["added_by_convexification"],
        },
        "bands": bands,
        "aggregate": dict(aggregate),
    }
    (OUT / "counterexample.json").write_text(json.dumps(witness_record, indent=2) + "\n")
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
