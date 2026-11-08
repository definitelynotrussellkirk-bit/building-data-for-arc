"""Visible-example solution for the post-repair review episode."""


def _count_horizontal_runs(grid, color):
    count = 0
    for row in grid:
        inside = False
        for value in row:
            if value == color:
                if not inside:
                    count += 1
                    inside = True
            else:
                inside = False
    return count


def solve(grid):
    """Encode horizontal run counts of 3, then 2, in a 2x3 tally."""
    values = (
        [3] * _count_horizontal_runs(grid, 3)
        + [2] * _count_horizontal_runs(grid, 2)
    )[:6]
    values += [0] * (6 - len(values))
    return [values[:3], values[3:]]
