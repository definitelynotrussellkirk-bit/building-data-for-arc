"""Visible-only solution for the reviewer blind task."""


def _smallest_row_period(grid):
    """Return the shortest period consistent with the observed row prefix."""
    height = len(grid)
    for period in range(1, height):
        if all(grid[row] == grid[row - period] for row in range(period, height)):
            return period
    return height


def solve(grid):
    """Continue the vertical row pattern by half its height and recolor 1 to 2."""
    if not grid:
        return []

    period = _smallest_row_period(grid)
    output_height = len(grid) + len(grid) // 2
    return [
        [2 if value == 1 else value for value in grid[row % period]]
        for row in range(output_height)
    ]
