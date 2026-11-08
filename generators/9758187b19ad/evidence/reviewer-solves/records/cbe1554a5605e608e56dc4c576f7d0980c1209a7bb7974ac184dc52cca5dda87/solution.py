"""Visible-example solution for reviewer episode 9758187b19ad."""

from __future__ import annotations

from typing import List

Grid = List[List[int]]


def _flip_horizontal(tile: Grid) -> Grid:
    return [row[::-1] for row in tile]


def _flip_vertical(tile: Grid) -> Grid:
    return tile[::-1]


def _rotate_clockwise(tile: Grid) -> Grid:
    # A h x w tile becomes w x h.
    return [list(row) for row in zip(*tile[::-1])]


def solve(grid: Grid) -> Grid:
    """Replace each 3/4/5/6 marker with a transformed copy of the source tile.

    The source tile is the bounding box of colors other than background 0 and
    marker colors 3--6. Marker 3 uses the tile unchanged, marker 4 mirrors it
    left/right, marker 5 mirrors it top/bottom, and marker 6 rotates it 90
    degrees clockwise. The marker coordinate is the transformed tile's
    top-left bounding-box coordinate. The original source tile is removed.
    """

    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    marker_colors = {3, 4, 5, 6}

    source_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and value not in marker_colors
    ]
    if not source_cells:
        return [[0] * width for _ in range(height)]

    r0 = min(r for r, _ in source_cells)
    r1 = max(r for r, _ in source_cells)
    c0 = min(c for _, c in source_cells)
    c1 = max(c for _, c in source_cells)
    tile = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]

    variants = {
        3: tile,
        4: _flip_horizontal(tile),
        5: _flip_vertical(tile),
        6: _rotate_clockwise(tile),
    }
    markers = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in marker_colors
    ]

    out = [[0] * width for _ in range(height)]
    for anchor_r, anchor_c, marker in markers:
        transformed = variants[marker]
        for dr, row in enumerate(transformed):
            for dc, value in enumerate(row):
                rr = anchor_r + dr
                cc = anchor_c + dc
                if not (0 <= rr < height and 0 <= cc < width):
                    raise ValueError(
                        f"transformed tile at marker {(anchor_r, anchor_c, marker)} "
                        "would leave the grid"
                    )
                if value != 0:
                    out[rr][cc] = value

    return out
