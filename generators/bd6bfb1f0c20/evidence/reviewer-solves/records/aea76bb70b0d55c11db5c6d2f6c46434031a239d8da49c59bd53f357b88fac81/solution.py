"""Visible-example solution for the prepared bd6bfb1f0c20 episode."""
from __future__ import annotations


def _components(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, cells))
    return components


def _perimeter(cells):
    occupied = set(cells)
    return sum(
        (row + dr, col + dc) not in occupied
        for row, col in occupied
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
    )


def solve(grid):
    """Return object colors in descending 4-neighbour perimeter order."""
    ranked = sorted(_components(grid), key=lambda item: (-_perimeter(item[1]), item[0]))
    return [[color for color, _cells in ranked]]
