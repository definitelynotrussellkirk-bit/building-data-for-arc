"""Independent, portable probes for task 51c5df6650a9.

The selected Racket rule remains the label authority.  This module mirrors its
observable behavior for regression tests and defines two explicit rival rules.
"""
from __future__ import annotations

from collections import deque
from pathlib import Path

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK_ID = "51c5df6650a9"
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def canonical_pairs():
    return _canonical_pairs(TASK_ID, root=find_root(__file__))


def legend(grid):
    """Nonzero first-row colors, preserving their left-to-right order."""
    seen = set()
    ordered = []
    for value in grid[0]:
        if value != 0 and value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def color_components(grid, color):
    h, w = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r in range(1, h)
        for c in range(w)
        if grid[r][c] == color
    }
    components = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        cells = {first}
        queue = deque([first])
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                point = (r + dr, c + dc)
                if point in remaining:
                    remaining.remove(point)
                    cells.add(point)
                    queue.append(point)
        components.append(cells)
    return sorted(components, key=lambda cells: min(cells))


def body_components(grid):
    components = []
    for color in sorted({value for row in grid[1:] for value in row if value}):
        for cells in color_components(grid, color):
            components.append((color, cells))
    return sorted(components, key=lambda item: min(item[1]))


def crop(grid, cells):
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    cell_set = set(cells)
    return [
        [grid[r][c] if (r, c) in cell_set else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


def pack_full(grid, colors):
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    left = 0
    for color in colors:
        components = color_components(grid, color)
        if not components:
            continue
        part = crop(grid, components[0])
        for r, row in enumerate(part, start=1):
            for c, value in enumerate(row, start=left):
                if r < h and c < w and value:
                    out[r][c] = value
        left += len(part[0]) + 1
    return out


def intended_output(grid):
    return pack_full(grid, legend(grid))


def fixed_columns_rival(grid):
    """Canonical-fitting shortcut: read only row-0 columns 0, 2 and 4."""
    colors = []
    for column in (0, 2, 4):
        if column < len(grid[0]):
            value = grid[0][column]
            if value and value not in colors:
                colors.append(value)
    return pack_full(grid, colors)


def body_scan_order_rival(grid):
    return pack_full(grid, [color for color, _ in body_components(grid)])


def source_path() -> Path:
    return Path(__file__).resolve().parents[1] / "generator.py"
