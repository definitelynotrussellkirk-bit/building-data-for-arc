"""Visible-example solution for bedf1922195c."""
from __future__ import annotations

from copy import deepcopy


def solve(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            rows = {r for r, _ in cells}
            cols = {c for _, c in cells}
            straight = len(rows) == 1 or len(cols) == 1
            if len(cells) >= 3 and len(cells) % 2 == 1 and straight:
                if len(rows) == 1:
                    cells.sort(key=lambda point: point[1])
                else:
                    cells.sort(key=lambda point: point[0])
                r, c = cells[len(cells) // 2]
                out[r][c] = 2
    return out
