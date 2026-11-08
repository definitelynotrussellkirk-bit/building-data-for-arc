"""Blind ARC solve for task b9b63ae52d91."""


def solve(grid):
    """Recolor 8s by whether their vertical-reflection partner is also 8."""
    height = len(grid)
    return [
        [
            0 if value == 0 else (2 if grid[height - 1 - row][col] == 8 else 5)
            for col, value in enumerate(values)
        ]
        for row, values in enumerate(grid)
    ]
