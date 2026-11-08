"""Visible-example solution for dfda42e49ff5."""
from __future__ import annotations


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]
    seen = set()

    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color == 0 or (row, column) in seen:
                continue

            stack = [(row, column)]
            seen.add((row, column))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if (nr, nc) in seen or grid[nr][nc] != color:
                        continue
                    seen.add((nr, nc))
                    stack.append((nr, nc))

            by_row = {}
            for rr, cc in cells:
                by_row.setdefault(rr, []).append(cc)
            for rr, columns in by_row.items():
                for cc in range(min(columns), max(columns) + 1):
                    output[rr][cc] = color

    return output
