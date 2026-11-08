"""Visible-example solve: hollow each same-colour connected rectangle."""
from __future__ import annotations

from collections import deque


def solve(grid):
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen = set()

    for row in range(height):
        for col in range(width):
            colour = grid[row][col]
            if colour == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
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

            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            top, bottom = min(rows), max(rows)
            left, right = min(cols), max(cols)
            for c in range(left, right + 1):
                output[top][c] = colour
                output[bottom][c] = colour
            for r in range(top, bottom + 1):
                output[r][left] = colour
                output[r][right] = colour

    return output
