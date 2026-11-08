"""Visible-example solution for the reviewer-authored episode."""
from __future__ import annotations


def solve(grid):
    """Recolor only blue 4-connected components shaped as exact vertical V3."""
    output = [list(row) for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            top = min(rr for rr, _ in cells)
            left = min(cc for _, cc in cells)
            normalized = sorted((rr - top, cc - left) for rr, cc in cells)
            if normalized == [(0, 0), (1, 0), (2, 0)]:
                for rr, cc in cells:
                    output[rr][cc] = 2

    return output
