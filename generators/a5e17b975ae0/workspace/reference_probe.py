"""Independent probes for a5e17b975ae0 reviewer tests.

This module is test tooling.  The canonical Racket program remains the label
source; ``python_output`` is an independently written parity oracle.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
import os
from pathlib import Path

TASK_ID = "a5e17b975ae0"


def load_generator(path: str | os.PathLike[str] | None = None):
    if path is None:
        path = os.environ.get("GENERATOR_UNDER_TEST")
    if path is None:
        path = Path(__file__).resolve().parents[1] / "generator.py"
    path = Path(path).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def python_output(grid):
    """Independent translation of the selected row-major keyed flood rule."""
    original = [list(row) for row in grid]
    out = deepcopy(original)
    h, w = len(original), len(original[0])
    seeds = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if original[r][c] not in (0, 5, 9)
    ]
    for sr, sc in seeds:
        color = original[sr][sc]
        queue = deque([(sr, sc)])
        seen = {(sr, sc)}
        while queue:
            r, c = queue.popleft()
            out[r][c] = color
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = r + dr, c + dc
                if not (0 <= rr < h and 0 <= cc < w) or (rr, cc) in seen:
                    continue
                value = original[rr][cc]
                if value in (5, 9) or value not in (0, color):
                    continue
                seen.add((rr, cc))
                queue.append((rr, cc))
    return out


def _components(cells):
    remaining = set(cells)
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    stack.append(point)
        result.append(component)
    return result


def frames(grid):
    nine = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9}
    result = []
    for component in _components(nine):
        r0 = min(r for r, _ in component)
        r1 = max(r for r, _ in component)
        c0 = min(c for _, c in component)
        c1 = max(c for _, c in component)
        border = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if component != border:
            raise ValueError("color-9 component is not one hollow rectangle")
        result.append((r0, c0, r1, c1))
    return sorted(result, key=lambda box: (box[1], box[0]))


def open_regions(grid, box):
    r0, c0, r1, c1 = box
    cells = {
        (r, c)
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
        if grid[r][c] not in (5, 9)
    }
    return _components(cells)


def seed_positions(grid):
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5, 9)
    ]


def region_seed_counts(grid):
    counts = []
    for box in frames(grid):
        for region in open_regions(grid, box):
            counts.append(sum(grid[r][c] not in (0, 5, 9) for r, c in region))
    return counts


def profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})
