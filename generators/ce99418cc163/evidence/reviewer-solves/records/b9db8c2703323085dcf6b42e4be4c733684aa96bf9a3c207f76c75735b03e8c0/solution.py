"""Simultaneous corner completion inferred from visible pairs; exposed reviewer."""
from itertools import combinations


def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('a nonempty rectangular grid is required')
    result = [list(row) for row in grid]
    red_columns = [{c for c,value in enumerate(row) if value == 2} for row in grid]
    for upper, lower in combinations(range(len(grid)), 2):
        # At least one shared red column supplies the fully occupied side.
        if not red_columns[upper].intersection(red_columns[lower]):
            continue
        for column in red_columns[upper] - red_columns[lower]:
            if grid[lower][column] == 0:
                result[lower][column] = 3
        for column in red_columns[lower] - red_columns[upper]:
            if grid[upper][column] == 0:
                result[upper][column] = 3
    return result
