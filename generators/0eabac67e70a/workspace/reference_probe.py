"""Independent test oracle for 0eabac67e70a.

This helper computes the selected Racket rule's span union without importing
production generator helpers.  It is test tooling, not label authority.
"""
from __future__ import annotations

from collections import defaultdict
import importlib.util
import os
from pathlib import Path

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK = "0eabac67e70a"
LOW_COLORS = frozenset({1, 2, 3, 4})
HIGH_COLORS = frozenset({5, 6, 7, 9})


def load_generator(path: str | os.PathLike[str] | None = None):
    root = find_root(__file__)
    target = Path(path or os.environ.get("GENERATOR_UNDER_TEST")
                  or root / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", target)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {target}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK, root=find_root(__file__), labeled_only=True)


def color_pairs(grid):
    points = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                points[value].append((r, c))
    return {color: tuple(cells) for color, cells in points.items()}


def _sign(value: int) -> int:
    return (value > 0) - (value < 0)


def reference_output(grid):
    """Independent Python translation of the pinned pair-span authority."""
    h = len(grid)
    w = len(grid[0])
    out = [[0] * w for _ in range(h)]
    for cells in color_pairs(grid).values():
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = sorted(cells)
        dr, dc = _sign(r2 - r1), _sign(c2 - c1)
        steps = max(abs(r2 - r1), abs(c2 - c1))
        for i in range(steps + 1):
            r, c = r1 + i * dr, c1 + i * dc
            if not (0 <= r < h and 0 <= c < w):
                raise ValueError("authority span escaped the input grid")
            out[r][c] = 8
    return out


def fixed_color_roles_output(grid):
    """Canonical-fitting shortcut: color 2 is horizontal, color 3 vertical."""
    h = len(grid)
    w = len(grid[0])
    out = [[0] * w for _ in range(h)]
    pairs = color_pairs(grid)
    cells = pairs.get(2, ())
    if len(cells) == 2 and cells[0][0] == cells[1][0]:
        r = cells[0][0]
        for c in range(min(cells[0][1], cells[1][1]), max(cells[0][1], cells[1][1]) + 1):
            out[r][c] = 8
    cells = pairs.get(3, ())
    if len(cells) == 2 and cells[0][1] == cells[1][1]:
        c = cells[0][1]
        for r in range(min(cells[0][0], cells[1][0]), max(cells[0][0], cells[1][0]) + 1):
            out[r][c] = 8
    return out


def observed(grid):
    pairs = color_pairs(grid)
    colors = set(pairs)
    if colors and colors <= LOW_COLORS:
        palette_kind = "low"
    elif colors and colors <= HIGH_COLORS:
        palette_kind = "high"
    else:
        palette_kind = "mixed_or_invalid"
    modes = set()
    for cells in pairs.values():
        if len(cells) != 2:
            modes.add("invalid")
            continue
        (r1, c1), (r2, c2) = cells
        if r1 == r2 or c1 == c2:
            modes.add("axis_aligned")
        elif abs(r2 - r1) == abs(c2 - c1):
            modes.add("diagonal")
        else:
            modes.add("invalid")
    orientation_family = next(iter(modes)) if len(modes) == 1 else "mixed_or_invalid"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_pairs": len(pairs),
        "palette_kind": palette_kind,
        "orientation_family": orientation_family,
    }


def swapped_roles_witness():
    grid = [[0] * 7 for _ in range(7)]
    grid[3][1] = grid[3][5] = 3
    grid[1][3] = grid[5][3] = 2
    return grid
