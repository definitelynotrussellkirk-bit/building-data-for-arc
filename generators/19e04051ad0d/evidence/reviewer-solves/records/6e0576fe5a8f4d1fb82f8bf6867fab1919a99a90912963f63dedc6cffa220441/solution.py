"""Visible-example solver for cyclic transfers between column regions."""
from collections import Counter


def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('Expected a nonempty rectangular grid')
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    regions = []
    start = None
    for col in range(len(grid[0]) + 1):
        boundary = col == len(grid[0]) or all(row[col] == background for row in grid)
        if boundary:
            if start is not None:
                regions.append(list(range(start, col)))
                start = None
        elif start is None:
            start = col
    if not regions:
        raise ValueError('No colored regions')
    colors = []
    for cols in regions:
        present = {row[col] for row in grid for col in cols} - {background}
        if len(present) != 1:
            raise ValueError('Expected one non-background color per region')
        colors.append(next(iter(present)))
    answer = [row[:] for row in grid]
    for i, cols in enumerate(regions):
        replacement = colors[(i + 1) % len(regions)]
        for r, row in enumerate(grid):
            for col in cols:
                if row[col] == background:
                    answer[r][col] = replacement
    return answer
