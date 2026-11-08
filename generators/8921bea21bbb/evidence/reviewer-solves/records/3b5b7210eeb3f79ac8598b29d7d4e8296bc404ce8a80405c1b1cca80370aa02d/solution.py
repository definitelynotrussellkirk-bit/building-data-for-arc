"""Visible-example solution for task 8921bea21bbb."""


def solve(grid):
    """Use the left panel as a binary mask over the right panel."""
    height = len(grid)
    separators = [
        column
        for column in range(len(grid[0]))
        if all(grid[row][column] == 9 for row in range(height))
    ]
    if len(separators) != 1:
        raise ValueError(f"expected one full-height 9 separator, got {separators}")
    separator = separators[0]
    if len(grid[0]) != 2 * separator + 1:
        raise ValueError("separator does not divide equal-width panels")
    return [
        [grid[row][separator + 1 + column] if grid[row][column] != 0 else 0
         for column in range(separator)]
        for row in range(height)
    ]
