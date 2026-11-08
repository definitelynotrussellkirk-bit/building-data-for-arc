"""Independent oracle and morphology probe for task 99f58784e7a0.

This file deliberately does not import implementation helpers from generator.py.
It recovers chambers directly from full color-8 wall rows/columns and applies the
written fill rule.  Tests use it to distinguish generator behavior from a copied
self-consistency check.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import sys
from typing import Any

TASK = "99f58784e7a0"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))

from reviewer_support import canonical_pairs as _canonical_pairs, find_root


LAYOUT_SPANS = {
    ("vertical_unequal", "canonical"): ((2, 3), (8,)),
    ("vertical_unequal", "expanded"): ((3, 4), (9,)),
    ("vertical_equal", "canonical"): ((3, 3), (7,)),
    ("vertical_equal", "expanded"): ((4, 4), (8,)),
    ("horizontal_three", "canonical"): ((8,), (3, 3, 2)),
    ("horizontal_three", "expanded"): ((9,), (4, 4, 3)),
    ("grid_2x2", "canonical"): ((3, 3), (4, 4)),
    ("grid_2x2", "expanded"): ((4, 4), (5, 5)),
}


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", source)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK, root=find_root(__file__))


def _validate_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors 0..9")
    return len(grid), width


def chamber_analysis(grid: Any) -> dict[str, Any]:
    """Recover the rectangular chambers and their single seed colors."""
    h, w = _validate_grid(grid)
    wall_rows = tuple(r for r in range(h) if all(grid[r][c] == 8 for c in range(w)))
    wall_cols = tuple(c for c in range(w) if all(grid[r][c] == 8 for r in range(h)))
    if not wall_rows or wall_rows[0] != 0 or wall_rows[-1] != h - 1:
        raise ValueError("top and bottom borders must be full color-8 rows")
    if not wall_cols or wall_cols[0] != 0 or wall_cols[-1] != w - 1:
        raise ValueError("left and right borders must be full color-8 columns")

    wall_cells = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if r in wall_rows or c in wall_cols
    }
    actual_eights = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8}
    if actual_eights != wall_cells:
        raise ValueError("every color-8 cell must belong to a complete wall row or column")

    row_spans = tuple(b - a - 1 for a, b in zip(wall_rows, wall_rows[1:]))
    col_spans = tuple(b - a - 1 for a, b in zip(wall_cols, wall_cols[1:]))
    if not row_spans or not col_spans or min(row_spans + col_spans) < 2:
        raise ValueError("walls must enclose chambers at least 2x2")

    chambers = []
    for ra, rb in zip(wall_rows, wall_rows[1:]):
        for ca, cb in zip(wall_cols, wall_cols[1:]):
            cells = tuple((r, c) for r in range(ra + 1, rb) for c in range(ca + 1, cb))
            seeds = tuple((r, c, grid[r][c]) for r, c in cells if grid[r][c] not in (0, 8))
            if len(seeds) != 1:
                raise ValueError(f"chamber {(ra, ca, rb, cb)} has {len(seeds)} seeds")
            if all(grid[r][c] != 0 for r, c in cells):
                raise ValueError("each chamber must contain background to fill")
            chambers.append({"bounds": (ra, ca, rb, cb), "cells": cells, "seed": seeds[0]})

    return {
        "height": h,
        "width": w,
        "wall_rows": wall_rows,
        "wall_cols": wall_cols,
        "row_spans": row_spans,
        "col_spans": col_spans,
        "chambers": tuple(chambers),
        "seed_colors": tuple(chamber["seed"][2] for chamber in chambers),
    }


def intended_output(grid: Any) -> list[list[int]]:
    analysis = chamber_analysis(grid)
    out = deepcopy(grid)
    for chamber in analysis["chambers"]:
        color = chamber["seed"][2]
        for r, c in chamber["cells"]:
            out[r][c] = color
    return out


def distinct_colors_only_rival(grid: Any) -> list[list[int]]:
    """Plausible shortcut: fill only when all chambers have unique colors."""
    analysis = chamber_analysis(grid)
    colors = analysis["seed_colors"]
    if len(set(colors)) != len(colors):
        return deepcopy(grid)
    return intended_output(grid)


def observed(grid: Any) -> dict[str, str]:
    analysis = chamber_analysis(grid)
    pair = (analysis["row_spans"], analysis["col_spans"])
    matches = [key for key, spans in LAYOUT_SPANS.items() if spans == pair]
    if len(matches) != 1:
        raise ValueError(f"grid has no unique declared layout/scale: {pair}")
    layout_profile, scale = matches[0]
    colors = analysis["seed_colors"]
    color_pattern = "distinct" if len(set(colors)) == len(colors) else "reused"
    return {
        "layout_profile": layout_profile,
        "scale": scale,
        "color_pattern": color_pattern,
    }


def connected_nonwall_components(grid: Any) -> list[set[tuple[int, int]]]:
    """Independent connected-region implementation used for one parity check."""
    h, w = _validate_grid(grid)
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 8}
    components = []
    while remaining:
        start = next(iter(remaining))
        todo = deque([start])
        remaining.remove(start)
        component = {start}
        while todo:
            r, c = todo.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    todo.append(nxt)
        components.append(component)
    return components
