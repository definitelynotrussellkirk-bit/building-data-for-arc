"""Visible-example solution for the post-repair rectangle-sort puzzle."""
from __future__ import annotations


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    objects = []

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
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            r1 = min(r for r, _ in cells)
            r2 = max(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            c2 = max(c for _, c in cells)
            crop = [list(source[c1 : c2 + 1]) for source in grid[r1 : r2 + 1]]
            objects.append((len(cells), r1, c1, crop))

    objects.sort(key=lambda item: item[:3])
    out_height = max(len(crop) for _, _, _, crop in objects)
    out_width = sum(len(crop[0]) for _, _, _, crop in objects) + len(objects) - 1
    output = [[0] * out_width for _ in range(out_height)]

    left = 0
    for _, _, _, crop in objects:
        for row, values in enumerate(crop):
            for col, value in enumerate(values):
                if value != 0:
                    output[row][left + col] = value
        left += len(crop[0]) + 1
    return output
