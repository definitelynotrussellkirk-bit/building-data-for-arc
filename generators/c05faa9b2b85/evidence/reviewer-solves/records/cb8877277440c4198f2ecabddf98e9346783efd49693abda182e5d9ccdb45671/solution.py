"""Visible-example solution for c05faa9b2b85."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill each non-1 component only when it has one distinct marker color."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [row[:] for row in grid]
    seen: set[tuple[int, int]] = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 1 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            colors: set[int] = set()
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                if grid[rr][cc] > 1:
                    colors.add(grid[rr][cc])
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            if len(colors) == 1:
                fill = next(iter(colors))
                for rr, cc in cells:
                    if grid[rr][cc] == 0:
                        output[rr][cc] = fill
    return output
