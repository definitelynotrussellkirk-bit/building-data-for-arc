"""Visible-example solver for the generated ARC task.

The input contains one or more hollow 4x4 colored frames and blue (1)
marker runs on the outside boundary.  Each marker selects the frame whose
span overlaps it and asks that frame to be repeated, at a stride of four,
toward that boundary.  Markers disappear from the output.
"""

from __future__ import annotations

from collections import deque
from typing import Iterable

Grid = list[list[int]]
Frame = tuple[int, int, int]  # top row, left column, color
Cell = tuple[int, int]


def _rectangular(grid: Grid) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a non-empty rectangular list of lists")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    return len(grid), width


def _is_hollow_frame(grid: Grid, top: int, left: int) -> int | None:
    """Return the frame color when this 4x4 window is a hollow square."""
    color = grid[top][left]
    if color in (0, 1):
        return None

    for dr in range(4):
        for dc in range(4):
            value = grid[top + dr][left + dc]
            border = dr in (0, 3) or dc in (0, 3)
            if border:
                if value != color:
                    return None
            elif value != 0:
                return None
    return color


def _find_frames(grid: Grid, height: int, width: int) -> list[Frame]:
    frames: list[Frame] = []
    for top in range(height - 3):
        for left in range(width - 3):
            color = _is_hollow_frame(grid, top, left)
            if color is not None:
                frames.append((top, left, color))
    if not frames:
        raise ValueError("no hollow 4x4 frame found")
    return frames


def _marker_components(grid: Grid, height: int, width: int) -> list[list[Cell]]:
    """Find 4-connected boundary components made from color 1."""
    boundary = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] == 1 and (r in (0, height - 1) or c in (0, width - 1))
    }
    components: list[list[Cell]] = []
    while boundary:
        start = min(boundary)
        boundary.remove(start)
        queue = deque([start])
        component = [start]
        while queue:
            r, c = queue.popleft()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in boundary:
                    boundary.remove((nr, nc))
                    queue.append((nr, nc))
                    component.append((nr, nc))
        components.append(sorted(component))
    return components


def _direction(component: list[Cell], height: int, width: int) -> tuple[int, int]:
    if all(r == 0 for r, _ in component):
        return -1, 0
    if all(r == height - 1 for r, _ in component):
        return 1, 0
    if all(c == 0 for _, c in component):
        return 0, -1
    if all(c == width - 1 for _, c in component):
        return 0, 1
    raise ValueError("a marker component must lie on exactly one outer edge")


def _overlap(a0: int, a1: int, b0: int, b1: int) -> int:
    return max(0, min(a1, b1) - max(a0, b0) + 1)


def _select_frame(component: list[Cell], direction: tuple[int, int], frames: list[Frame]) -> Frame:
    """Select the frame whose perpendicular span best overlaps the marker."""
    dr, _ = direction
    if dr:
        lo = min(c for _, c in component)
        hi = max(c for _, c in component)
        scored = [(_overlap(lo, hi, left, left + 3), frame) for frame in frames for _, left, _ in [frame]]
    else:
        lo = min(r for r, _ in component)
        hi = max(r for r, _ in component)
        scored = [(_overlap(lo, hi, top, top + 3), frame) for frame in frames for top, _, _ in [frame]]

    best_score = max(score for score, _ in scored)
    candidates = [frame for score, frame in scored if score == best_score and score > 0]
    if len(candidates) != 1:
        raise ValueError("marker does not identify exactly one frame by overlap")
    return candidates[0]


def _draw_frame(output: Grid, top: int, left: int, color: int) -> None:
    height, width = len(output), len(output[0])
    for dr in range(4):
        for dc in range(4):
            if dr not in (0, 3) and dc not in (0, 3):
                continue
            r, c = top + dr, left + dc
            if 0 <= r < height and 0 <= c < width:
                output[r][c] = color


def _intersects_grid(top: int, left: int, height: int, width: int) -> bool:
    return top <= height - 1 and top + 3 >= 0 and left <= width - 1 and left + 3 >= 0


def solve(grid: Grid) -> Grid:
    height, width = _rectangular(grid)
    frames = _find_frames(grid, height, width)
    markers = _marker_components(grid, height, width)

    output = [[0 for _ in range(width)] for _ in range(height)]
    for top, left, color in frames:
        _draw_frame(output, top, left, color)

    for component in markers:
        dr, dc = _direction(component, height, width)
        top, left, color = _select_frame(component, (dr, dc), frames)
        top += 4 * dr
        left += 4 * dc
        while _intersects_grid(top, left, height, width):
            _draw_frame(output, top, left, color)
            top += 4 * dr
            left += 4 * dc

    return output
