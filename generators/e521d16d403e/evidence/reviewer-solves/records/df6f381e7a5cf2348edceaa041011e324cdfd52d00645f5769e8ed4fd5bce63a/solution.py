"""Visible-example solution for the exposed post-repair episode."""
from __future__ import annotations


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
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
                    if (0 <= nr < height and 0 <= nc < width and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            r0 = min(r for r, _ in cells)
            r1 = max(r for r, _ in cells)
            c0 = min(c for _, c in cells)
            c1 = max(c for _, c in cells)
            crop = [line[c0:c1 + 1] for line in grid[r0:r1 + 1]]
            if c1 > c0 and all(line == line[::-1] for line in crop):
                objects.append((len(cells), crop))

    if not objects:
        raise ValueError("no left-right symmetric object with width greater than one")
    return max(objects, key=lambda item: item[0])[1]
