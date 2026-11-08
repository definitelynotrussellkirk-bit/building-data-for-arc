"""Independent oracle and probes for cfd0943c5b14.

This module deliberately does not import implementation helpers from generator.py.
The Python oracle supplements, but never replaces, the canonical Racket authority.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK = "cfd0943c5b14"
sys.path.insert(0, str(ROOT / "shared/runtime"))
from reviewer_support import canonical_pairs as _canonical_pairs, find_root

OFFSETS = ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1))


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK, root=find_root(__file__))


def seeds(grid):
    return [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]


def footprint(grid, r, c):
    h, w = len(grid), len(grid[0])
    return frozenset(
        (r + dr, c + dc)
        for dr, dc in OFFSETS
        if 0 <= r + dr < h and 0 <= c + dc < w
    )


def x_output(grid, *, keep=lambda _r, _c, _value, _h, _w: True):
    """Fresh cyan union of diagonal-X stamps selected by an explicit predicate."""
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for r, c, value in seeds(grid):
        if keep(r, c, value, h, w):
            for rr, cc in footprint(grid, r, c):
                out[rr][cc] = 8
    return out


def ignored_cyan_output(grid):
    return x_output(grid, keep=lambda _r, _c, value, _h, _w: value != 8)


def ignored_boundary_output(grid):
    return x_output(
        grid,
        keep=lambda r, c, _value, h, w: 0 < r < h - 1 and 0 < c < w - 1,
    )


def only_color_three_output(grid):
    return x_output(grid, keep=lambda _r, _c, value, _h, _w: value == 3)


def boundary_kind(grid, r, c):
    h, w = len(grid), len(grid[0])
    if r in (0, h - 1) and c in (0, w - 1):
        return "corner"
    if r in (0, h - 1) or c in (0, w - 1):
        return "edge"
    return "interior"


def overlapping_pair_count(grid):
    pts = seeds(grid)
    count = 0
    for i, (r1, c1, _v1) in enumerate(pts):
        f1 = footprint(grid, r1, c1)
        for r2, c2, _v2 in pts[i + 1 :]:
            if f1 & footprint(grid, r2, c2):
                count += 1
    return count


def observed(grid):
    pts = seeds(grid)
    kinds = [boundary_kind(grid, r, c) for r, c, _ in pts]
    values = {value for _r, _c, value in pts}
    if values == {3} and set(kinds) == {"interior"}:
        scene = "canonical"
    elif 8 not in values and kinds.count("edge") == 1 and kinds.count("corner") == 0:
        scene = "edge_seed"
    elif 8 in values and len(values) >= 2 and set(kinds) == {"interior"} and overlapping_pair_count(grid):
        scene = "mixed_overlap"
    elif 8 not in values and kinds.count("corner") == 1 and kinds.count("edge") == 0:
        scene = "corner_seed"
    elif values == {8} and set(kinds) == {"interior"}:
        scene = "cyan_interior"
    else:
        scene = "unclassified"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "seed_count": len(pts),
        "scene": scene,
    }


def canonical_shortcut_fits():
    solvers = {
        "ignore_cyan_seed": ignored_cyan_output,
        "ignore_boundary_seeds": ignored_boundary_output,
        "only_color_three": only_color_three_output,
    }
    return {
        name: all(solver(deepcopy(pair["input"])) == pair["output"] for pair in canonical_pairs())
        for name, solver in solvers.items()
    }
