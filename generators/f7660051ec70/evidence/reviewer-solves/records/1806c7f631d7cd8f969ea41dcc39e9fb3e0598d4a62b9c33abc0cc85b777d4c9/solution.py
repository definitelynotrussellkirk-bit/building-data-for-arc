"""Visible-example solution for the reviewer-authored ARC puzzle."""
from __future__ import annotations

from copy import deepcopy


def _one_components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            yield cells


def solve(grid):
    """Fill the interior of every rectangular 1-frame containing a 2 seed."""
    if not grid or not grid[0]:
        return deepcopy(grid)

    result = deepcopy(grid)
    for component in _one_components(grid):
        top = min(row for row, _ in component)
        bottom = max(row for row, _ in component)
        left = min(col for _, col in component)
        right = max(col for _, col in component)

        # The visible examples use color-1 connected components as rectangular
        # borders.  A color-2 marker anywhere strictly inside activates the frame.
        active = any(
            grid[row][col] == 2
            for row in range(top + 1, bottom)
            for col in range(left + 1, right)
        )
        if not active:
            continue
        for row in range(top + 1, bottom):
            for col in range(left + 1, right):
                if result[row][col] == 0:
                    result[row][col] = 3
    return result
