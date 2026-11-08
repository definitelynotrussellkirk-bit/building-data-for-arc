"""Exposed post-repair solve, checked only against visible demonstration pairs."""


def solve(grid):
    height, width = len(grid), len(grid[0])
    out = [[0 for _ in range(width)] for _ in range(height)]
    for middle_row in range(1, height - 1):
        for middle_col in range(1, width - 1):
            color = grid[middle_row][middle_col]
            if color == 0:
                continue
            neighborhood = [grid[r][c]
                            for r in range(middle_row - 1, middle_row + 2)
                            for c in range(middle_col - 1, middle_col + 2)]
            if any(value != color for value in neighborhood):
                continue
            for r in (middle_row - 1, middle_row + 1):
                for c in (middle_col - 1, middle_col + 1):
                    out[r][c] = color
    return out
