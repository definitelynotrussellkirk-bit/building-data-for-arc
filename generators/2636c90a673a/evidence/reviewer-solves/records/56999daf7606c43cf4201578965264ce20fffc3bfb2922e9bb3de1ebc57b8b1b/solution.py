"""Visible-example solution for task 2636c90a673a."""


def solve(grid):
    """Drop row zero and retain, in order, columns marked blue (1)."""
    if not grid or not grid[0]:
        return []
    selected = [column for column, value in enumerate(grid[0]) if value == 1]
    return [[row[column] for column in selected] for row in grid[1:]]
