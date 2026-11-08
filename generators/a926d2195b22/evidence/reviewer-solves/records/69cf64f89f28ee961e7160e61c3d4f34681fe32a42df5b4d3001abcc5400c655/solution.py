"""Visible-example solution for a926d2195b22."""
from copy import deepcopy


def solve(grid):
    output = deepcopy(grid)
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []

    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(sorted(cells))

    if not components:
        return output
    target = min(components, key=lambda cells: (len(cells), cells[0]))
    for row, col in target:
        output[row][col] = 9
    return output
