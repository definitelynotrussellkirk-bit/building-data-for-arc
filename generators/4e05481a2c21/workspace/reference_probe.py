"""Independent probes for generator 4e05481a2c21.

This module is reviewer tooling, not label authority.  It intentionally derives
connected components, enclosed background regions, outputs, rivals, and visible
axis observations without importing helpers from the generator under review.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
from typing import Iterable

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK_ID = "4e05481a2c21"
PALETTE_BY_COLORS = {
    frozenset((2, 3)): "canonical",
    frozenset((4, 6)): "warm",
    frozenset((1, 8)): "cool",
    frozenset((5, 9)): "varied",
}


def load_generator(path: str | os.PathLike | None = None):
    """Load the selected generator file, honoring the portable-test override."""
    target = Path(path or Path(__file__).resolve().parents[1] / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_4e05481a2c21", target)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {target}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty grid")
    width = len(grid[0]) if isinstance(grid[0], (list, tuple)) else 0
    if not width or any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("expected integer ARC colors")


def components(grid):
    """Return same-color 4-connected components as (color, frozenset(cells))."""
    _validate_grid(grid)
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = [(row, col)]
            seen.add((row, col))
            cells = []
            for rr, cc in queue:
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append((color, frozenset(cells)))
    return result


def bbox(cells: Iterable[tuple[int, int]]):
    cells = tuple(cells)
    if not cells:
        raise ValueError("empty cells")
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def enclosed_regions(component_cells):
    """Find 4-connected zero regions enclosed inside one component's bbox."""
    occupied = set(component_cells)
    r0, c0, r1, c1 = bbox(occupied)
    zeros = {
        (row, col)
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
        if (row, col) not in occupied
    }
    seen = set()
    regions = []
    for start in sorted(zeros):
        if start in seen:
            continue
        queue = [start]
        seen.add(start)
        region = []
        touches_bbox = False
        for row, col in queue:
            region.append((row, col))
            touches_bbox |= row in (r0, r1) or col in (c0, c1)
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = row + dr, col + dc
                if nxt in zeros and nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        if not touches_bbox:
            regions.append(frozenset(region))
    return regions


def object_records(grid):
    records = []
    for color, cells in components(grid):
        r0, c0, r1, c1 = bbox(cells)
        regions = enclosed_regions(cells)
        records.append({
            "color": color,
            "cells": cells,
            "bbox": (r0, c0, r1, c1),
            "regions": regions,
        })
    return sorted(records, key=lambda record: record["bbox"][1])


def _normalized(cells):
    r0, c0, r1, c1 = bbox(cells)
    return frozenset((row - r0, col - c0) for row, col in cells), r1 - r0 + 1, c1 - c0 + 1


def _pack(items):
    if not items:
        return []
    height = max(item[1] for item in items)
    width = sum(item[2] for item in items) + len(items) - 1
    output = [[0] * width for _ in range(height)]
    left = 0
    for shape, shape_h, shape_w, color in items:
        for row, col in shape:
            output[row][left + col] = color
        left += shape_w + 1
    return output


def reference_output(grid):
    """Independent Python mirror of the selected canonical rule."""
    items = []
    for record in object_records(grid):
        holes = frozenset().union(*record["regions"]) if record["regions"] else frozenset()
        if not holes:
            continue
        shape, height, width = _normalized(holes)
        items.append((shape, height, width, record["color"]))
    return _pack(items)


def fill_hole_bbox_rival(grid):
    """Wrong rule: replace every union of enclosed holes by its full bbox."""
    items = []
    for record in object_records(grid):
        holes = frozenset().union(*record["regions"]) if record["regions"] else frozenset()
        if not holes:
            continue
        _, height, width = _normalized(holes)
        items.append((frozenset((r, c) for r in range(height) for c in range(width)),
                      height, width, record["color"]))
    return _pack(items)


def largest_region_rival(grid):
    """Wrong rule: keep only the largest enclosed region per object."""
    items = []
    for record in object_records(grid):
        if not record["regions"]:
            continue
        region = sorted(record["regions"], key=lambda cells: (-len(cells), sorted(cells)))[0]
        shape, height, width = _normalized(region)
        items.append((shape, height, width, record["color"]))
    return _pack(items)


def all_bbox_zeros_rival(grid):
    """Wrong rule: treat every zero in an object's bbox as a hole."""
    items = []
    for record in object_records(grid):
        r0, c0, r1, c1 = record["bbox"]
        zeros = frozenset(
            (row, col)
            for row in range(r0, r1 + 1)
            for col in range(c0, c1 + 1)
            if grid[row][col] == 0
        )
        if not zeros:
            continue
        shape, height, width = _normalized(zeros)
        items.append((shape, height, width, record["color"]))
    return _pack(items)


def observed(grid):
    """Recover the exact advertised axes solely from returned pixels."""
    records = object_records(grid)
    colors = frozenset(record["color"] for record in records)
    if colors not in PALETTE_BY_COLORS:
        raise ValueError(f"unrecognized palette {sorted(colors)}")
    if any(len(record["regions"]) > 1 for record in records):
        pattern = "split"
    else:
        nonrectangular = False
        for record in records:
            holes = frozenset().union(*record["regions"]) if record["regions"] else frozenset()
            if holes:
                _, height, width = _normalized(holes)
                nonrectangular |= len(holes) != height * width
        pattern = "notched" if nonrectangular else "rectangle"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "palette_kind": PALETTE_BY_COLORS[colors],
        "pattern_kind": pattern,
    }


def has_exterior_bbox_zero(grid):
    for record in object_records(grid):
        r0, c0, r1, c1 = record["bbox"]
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                if grid[row][col] != 0:
                    continue
                if row in (r0, r1) or col in (c0, c1):
                    return True
    return False


def make_labeled(module, seed, start, count, *, difficulty="medium"):
    """Materialize deterministic local pairs with the independent oracle."""
    pairs = []
    for sample_index in range(start, start + count):
        grid = module.generate(seed, sample_index, difficulty=difficulty)
        pairs.append({"input": deepcopy(grid), "output": reference_output(grid)})
    return pairs
