"""Blind solution for task 778a00c38b8d.

Recolor each 4-connected red (2) component green (3) exactly when that
component touches at least two distinct borders of the grid.  All other cells
are preserved.
"""


def solve(grid):
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    out = [row[:] for row in grid]
    seen = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 2 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            component = []
            borders = set()

            while stack:
                r, c = stack.pop()
                component.append((r, c))
                if r == 0:
                    borders.add("top")
                if r == height - 1:
                    borders.add("bottom")
                if c == 0:
                    borders.add("left")
                if c == width - 1:
                    borders.add("right")

                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 2
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            if len(borders) >= 2:
                for r, c in component:
                    out[r][c] = 3

    return out
