"""Visible-example solution for task 46580cfcca75."""
from __future__ import annotations


def solve(grid):
    """Replace each nonzero four-connected block by its bbox perimeter."""
    height = len(grid)
    width = len(grid[0])
    output = [[0] * width for _ in range(height)]
    seen = set()
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            r1, r2 = min(rows), max(rows)
            c1, c2 = min(cols), max(cols)
            for r in range(r1, r2 + 1):
                output[r][c1] = color
                output[r][c2] = color
            for c in range(c1, c2 + 1):
                output[r1][c] = color
                output[r2][c] = color
    return output
