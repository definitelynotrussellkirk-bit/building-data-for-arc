"""Visible-example solution for ARC task 0162460030af."""
from copy import deepcopy


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    objects = []

    for row in range(height):
        for column in range(width):
            if grid[row][column] == 0 or (row, column) in seen:
                continue
            stack = [(row, column)]
            seen.add((row, column))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            objects.append(cells)

    objects.sort(key=lambda cells: min(column for _, column in cells))
    output = deepcopy(grid)
    count = len(objects)
    for index, cells in enumerate(objects):
        color = 8 if (count - index) % 2 == 1 else 2
        for row, column in cells:
            output[row][column] = color
    return output
