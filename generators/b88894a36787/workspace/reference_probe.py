"""Independent geometry oracle and diagnostics for task b88894a36787.

This module is test/review tooling.  Production labels remain owned by the
pinned Racket rule; the mirror exists so regressions have small, readable
counterexamples and do not need to introspect generator internals.
"""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import os
from pathlib import Path


def load_generator(default_path: Path):
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", default_path))
    spec = spec_from_file_location("generator_b88894a36787_under_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {path}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def header_entries(grid):
    """Return (column, color, target_row, target_col-or-None) in header order."""
    h, w = len(grid), len(grid[0])
    body = [(r, c, grid[r][c]) for r in range(1, h) for c in range(w)
            if grid[r][c] != 0]
    entries = []
    for c, color in enumerate(grid[0]):
        if color == 0:
            continue
        dot = next((item for item in body if item[2] == color), None)
        if dot is None:
            entries.append((c, color, h - 1, None))
        else:
            entries.append((c, color, dot[0], dot[1]))
    return entries


def geometry_output(grid):
    """Pure Python mirror of the selected Racket rule's first-match semantics."""
    h, w = len(grid), len(grid[0])
    entries = header_entries(grid)
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r in range(h):
        for c in range(w):
            for header_col, color, target_row, target_col in entries:
                vertical = c == header_col and r <= target_row
                horizontal = (
                    target_col is not None
                    and r == target_row
                    and min(header_col, target_col) <= c <= max(header_col, target_col)
                )
                if vertical or horizontal:
                    out[r][c] = color
                    break
    return out


def observed(grid):
    entries = header_entries(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_markers": len(entries),
        "n_missing": sum(target_col is None for _, _, _, target_col in entries),
        "left_dots": sum(target_col == 0 for _, _, _, target_col in entries),
        "right_dots": sum(target_col == len(grid[0]) - 1
                          for _, _, _, target_col in entries),
    }


def path_cells(entry):
    header_col, _color, target_row, target_col = entry
    cells = {(r, header_col) for r in range(target_row + 1)}
    if target_col is not None:
        cells.update((target_row, c)
                     for c in range(min(header_col, target_col),
                                    max(header_col, target_col) + 1))
    return cells


def path_overlaps(grid):
    """Return colored path intersections; lawful sampler instances have none."""
    entries = header_entries(grid)
    result = []
    for i, left in enumerate(entries):
        for right in entries[i + 1:]:
            overlap = sorted(path_cells(left) & path_cells(right))
            if overlap:
                result.append((left[1], right[1], overlap))
    return result
