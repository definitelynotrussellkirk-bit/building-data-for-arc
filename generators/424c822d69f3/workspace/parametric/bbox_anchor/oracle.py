"""Independent semantics for the proposed rectangle-anchor rule family."""
from __future__ import annotations

from copy import deepcopy

ANCHORS = ("midpoint", "left_edge", "right_edge")


def validate_anchor(anchor: str) -> str:
    if type(anchor) is not str:
        raise TypeError("anchor must be a string")
    if anchor not in ANCHORS:
        raise ValueError(f"anchor must be one of {ANCHORS}, got {anchor!r}")
    return anchor


def components(grid: list[list[int]], color: int = 5) -> list[tuple[tuple[int, int], ...]]:
    unseen = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    found: list[tuple[tuple[int, int], ...]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        pending = [start]
        cells = []
        while pending:
            row, col = pending.pop()
            cells.append((row, col))
            for point in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if point in unseen:
                    unseen.remove(point)
                    pending.append(point)
        found.append(tuple(sorted(cells)))
    return sorted(found, key=lambda cells: (min(col for _, col in cells), min(row for row, _ in cells)))


def bbox(cells: tuple[tuple[int, int], ...]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def markers(grid: list[list[int]]) -> list[tuple[int, int]]:
    return [(col, value) for col, value in enumerate(grid[0]) if value not in (0, 5)]


def anchor_column(c0: int, c1: int, anchor: str) -> int:
    validate_anchor(anchor)
    if anchor == "left_edge":
        return c0
    if anchor == "right_edge":
        return c1
    return (c0 + c1) // 2


def nearest_marker_index(marker_cols: list[int], column: int) -> int | None:
    distances = [abs(marker - column) for marker in marker_cols]
    best = min(distances)
    return distances.index(best) if distances.count(best) == 1 else None


def independent_output(grid: list[list[int]], anchor: str) -> list[list[int]]:
    """Apply one anchor rule without importing the production generator."""
    validate_anchor(anchor)
    out = deepcopy(grid)
    legend = markers(grid)
    if not legend:
        raise ValueError("at least one marker is required")
    marker_cols = [col for col, _ in legend]
    for cells in components(grid):
        _r0, c0, _r1, c1 = bbox(cells)
        point = anchor_column(c0, c1, anchor)
        nearest = nearest_marker_index(marker_cols, point)
        if nearest is None:
            raise ValueError(f"exact nearest-marker tie under anchor={anchor}")
        color = legend[nearest][1]
        for row, col in cells:
            out[row][col] = color
    return out
