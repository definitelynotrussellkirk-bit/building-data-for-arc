"""Visible-example solution for the post-repair episode."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    seen: set[tuple[int, int]] = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            r0 = min(rr for rr, _ in cells)
            r1 = max(rr for rr, _ in cells)
            c0 = min(cc for _, cc in cells)
            c1 = max(cc for _, cc in cells)
            interior_area = max(0, r1 - r0 - 1) * max(0, c1 - c0 - 1)
            fill = 5 if interior_area == 1 else 7
            for rr in range(r0 + 1, r1):
                for cc in range(c0 + 1, c1):
                    if grid[rr][cc] == 0:
                        output[rr][cc] = fill
    return output
