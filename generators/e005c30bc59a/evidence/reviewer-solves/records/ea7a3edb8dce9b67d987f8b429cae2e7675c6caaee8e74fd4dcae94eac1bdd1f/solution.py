"""Visible-example-only solver for blind task e005c30bc59a.

A unique nonzero color outside {1, 2, 5} is the trace color.  Starting at
that cell, the trace reaches the nearest axis-aligned blue/red guide.  Each
subsequent segment turns ninety degrees and aims at an unused guide of the
opposite blue/red color; once that alternating color is exhausted, gray is
the terminal guide.  If the selected next guide is not on the required axis,
the trace still turns toward it but runs to the border.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Iterable

Grid = list[list[int]]
Point = tuple[int, int]
Direction = tuple[int, int]

_GUIDE_COLORS = {1, 2, 5}


def _positions(grid: Grid, color: int) -> list[Point]:
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]


def _direction(a: Point, b: Point) -> Direction:
    """Return the cardinal direction from *a* to axis-aligned *b*."""
    ar, ac = a
    br, bc = b
    if ar == br and ac != bc:
        return (0, 1 if bc > ac else -1)
    if ac == bc and ar != br:
        return (1 if br > ar else -1, 0)
    raise ValueError(f"points are not axis aligned: {a}, {b}")


def _initial_target(origin: Point, candidates: Iterable[Point]) -> Point | None:
    aligned = [
        point
        for point in candidates
        if point != origin and (point[0] == origin[0] or point[1] == origin[1])
    ]
    if not aligned:
        return None
    return min(
        aligned,
        key=lambda point: (
            abs(point[0] - origin[0]) + abs(point[1] - origin[1]),
            point[0],
            point[1],
        ),
    )


def _next_target(
    current: Point,
    incoming: Direction,
    candidates: Iterable[Point],
) -> tuple[Point, Direction, bool] | None:
    """Choose the next guide and the mandatory perpendicular turn.

    Axis-aligned candidates in either legal turn direction are preferred.  If
    no candidate is aligned, choose the candidate requiring the smallest move
    on the new axis and turn toward it; that ray necessarily exits the board.
    """
    points = [point for point in candidates if point != current]
    if not points:
        return None

    cr, cc = current
    dr, dc = incoming
    if dr:  # Arrived vertically, so the next segment is horizontal.
        aligned = [point for point in points if point[0] == cr and point[1] != cc]
        if aligned:
            target = min(aligned, key=lambda p: (abs(p[1] - cc), p[0], p[1]))
            return target, (0, 1 if target[1] > cc else -1), True
        usable = [point for point in points if point[1] != cc]
        if not usable:
            return None
        target = min(
            usable,
            key=lambda p: (abs(p[1] - cc), abs(p[0] - cr), p[0], p[1]),
        )
        return target, (0, 1 if target[1] > cc else -1), False

    # Arrived horizontally, so the next segment is vertical.
    aligned = [point for point in points if point[1] == cc and point[0] != cr]
    if aligned:
        target = min(aligned, key=lambda p: (abs(p[0] - cr), p[0], p[1]))
        return target, (1 if target[0] > cr else -1, 0), True
    usable = [point for point in points if point[0] != cr]
    if not usable:
        return None
    target = min(
        usable,
        key=lambda p: (abs(p[0] - cr), abs(p[1] - cc), p[0], p[1]),
    )
    return target, (1 if target[0] > cr else -1, 0), False


def _paint_segment(
    output: Grid,
    start: Point,
    direction: Direction,
    trace_color: int,
    target: Point | None,
) -> Point | None:
    """Paint zeros from start until target or border; preserve guide cells."""
    height, width = len(output), len(output[0])
    row, col = start
    dr, dc = direction
    row += dr
    col += dc

    while 0 <= row < height and 0 <= col < width:
        if target is not None and (row, col) == target:
            return target
        if output[row][col] == 0:
            output[row][col] = trace_color
        row += dr
        col += dc
    return None


def solve(grid: Grid) -> Grid:
    if not grid or not grid[0]:
        return deepcopy(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    output = deepcopy(grid)
    trace_cells = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0 and value not in _GUIDE_COLORS
    ]
    if len(trace_cells) != 1:
        return output

    row, col, trace_color = trace_cells[0]
    current = (row, col)
    remaining = {
        1: set(_positions(grid, 1)),
        2: set(_positions(grid, 2)),
        5: set(_positions(grid, 5)),
    }

    first = _initial_target(current, remaining[1] | remaining[2])
    if first is None:
        return output
    incoming = _direction(current, first)
    reached = _paint_segment(output, current, incoming, trace_color, first)
    if reached is None:
        return output
    current = reached
    current_color = grid[current[0]][current[1]]
    remaining[current_color].discard(current)

    # Every turn consumes a guide.  A small fixed cap also makes malformed
    # inputs safe even if a future extension changes the bookkeeping.
    for _ in range(sum(len(points) for points in remaining.values()) + 1):
        if current_color == 5:
            break
        opposite = 2 if current_color == 1 else 1
        next_color = opposite if remaining[opposite] else 5
        choice = _next_target(current, incoming, remaining[next_color])
        if choice is None:
            break
        target, outgoing, aligned = choice
        reached = _paint_segment(
            output,
            current,
            outgoing,
            trace_color,
            target if aligned else None,
        )
        if reached is None:
            break
        current = reached
        current_color = next_color
        remaining[current_color].discard(current)
        incoming = outgoing

    return output
