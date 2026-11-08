"""Independent review helpers for ``dfc3ce537883``.

This module is test tooling, not label authority.  It loads canonical pairs
through the portable public helper, derives the mirror rule directly from the
visible color-9 divider, and implements two deliberately wrong rivals that fit
all public examples.  ``GENERATOR_UNDER_TEST`` may point at retained source for
red/green comparisons in an extracted review packet.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib
import importlib.util
import os
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK_ID = "dfc3ce537883"
ROOT = find_root(__file__)


def load_generator(path: str | os.PathLike[str] | None = None):
    selected = path or os.environ.get("GENERATOR_UNDER_TEST")
    if selected:
        source = Path(selected)
        if not source.is_absolute():
            source = (Path.cwd() / source).resolve()
        spec = importlib.util.spec_from_file_location(
            f"reviewed_{TASK_ID}_{abs(hash(str(source)))}", source
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot import generator from {source}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    candidates = (
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    source = next((candidate for candidate in candidates if candidate.is_file()), None)
    if source is not None:
        spec = importlib.util.spec_from_file_location(
            f"reviewed_{TASK_ID}_selected", source
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot import generator from {source}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    )


def canonical_pairs() -> list[dict[str, Any]]:
    return _canonical_pairs(TASK_ID, root=ROOT, variant=0)


def divider_column(grid: list[list[int]]) -> int:
    if not grid or not grid[0]:
        raise ValueError("grid must be nonempty")
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    columns = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(columns) != 1:
        raise ValueError(f"expected one full color-9 divider, found {len(columns)}")
    return columns[0]


def source_cells(grid: list[list[int]]) -> set[tuple[int, int]]:
    axis = divider_column(grid)
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row[:axis])
        if value not in (0, 9)
    }


def component_sets(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    queue.append(point)
        result.append(component)
    return result


def reference_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python statement of the selected endpoint rule."""
    axis = divider_column(grid)
    out = deepcopy(grid)
    for r, c in source_cells(grid):
        mirror = 2 * axis - c
        if not 0 <= mirror < len(grid[0]):
            raise ValueError(f"source cell {(r, c)} has clipped mirror {mirror}")
        out[r][mirror] = grid[r][c]
    return out


def observed_axes(grid: list[list[int]]) -> dict[str, int | str]:
    axis = divider_column(grid)
    cells = source_cells(grid)
    colors = {grid[r][c] for r, c in cells}
    components = component_sets(cells)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_cells": len(cells),
        "n_colors": len(colors),
        "layout": "connected" if len(components) == 1 else "split" if len(components) == 2 else "other",
        "axis_position": "center" if axis == len(grid[0]) // 2 else "off_center",
    }


def largest_component_only(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rival: reflect only the largest/first source component."""
    axis = divider_column(grid)
    components = component_sets(source_cells(grid))
    chosen = min(components, key=lambda cells: (-len(cells), min(cells)))
    out = deepcopy(grid)
    for r, c in chosen:
        out[r][2 * axis - c] = grid[r][c]
    return out


def monochrome_copy(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rival: preserve geometry but paint every copy the first color."""
    axis = divider_column(grid)
    cells = sorted(source_cells(grid))
    color = grid[cells[0][0]][cells[0][1]]
    out = deepcopy(grid)
    for r, c in cells:
        out[r][2 * axis - c] = color
    return out
