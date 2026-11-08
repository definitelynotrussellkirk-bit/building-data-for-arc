from copy import deepcopy


def solve(grid):
    """Recolor color-1 cells strictly below their occupied-row midpoint."""
    rows = [r for r, row in enumerate(grid) for value in row if value == 1]
    if not rows:
        return deepcopy(grid)
    midpoint_twice = min(rows) + max(rows)
    return [
        [2 if value == 1 and 2 * r > midpoint_twice else value
         for value in row]
        for r, row in enumerate(grid)
    ]
