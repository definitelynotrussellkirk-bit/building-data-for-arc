"""Visible-example solution for review task 1856980929fe."""

from __future__ import annotations

from collections import deque
from typing import List

Grid = List[List[int]]


def _components(grid: Grid) -> list[list[tuple[int, int]]]:
    """Return 4-connected nonzero same-colour components."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            colour = grid[row][col]
            queue = deque([(row, col)])
            seen.add((row, col))
            component: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == colour
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(component)
    return result


def solve(grid: Grid) -> Grid:
    """Fan each solid seed rectangle downward along both corner diagonals.

    A rectangle of height ``h`` and width ``w`` is copied at offsets
    ``(k*h, -k*w)`` and ``(k*h, +k*w)`` for every positive ``k`` whose copy
    intersects the canvas.  Boundary copies are clipped rather than discarded.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height, width = len(grid), len(grid[0])
    output = [row[:] for row in grid]

    for component in _components(grid):
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)
        rect_h, rect_w = bottom - top + 1, right - left + 1
        colour = grid[top][left]

        # The examples use filled rectangles.  Copy the whole bounding rectangle
        # so later overlaps naturally form the union visible in the outputs.
        step = 1
        while top + step * rect_h < height:
            new_top = top + step * rect_h
            for new_left in (left - step * rect_w, left + step * rect_w):
                for r in range(new_top, min(new_top + rect_h, height)):
                    for c in range(max(new_left, 0), min(new_left + rect_w, width)):
                        output[r][c] = colour
            step += 1

    return output
