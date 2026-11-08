"""Visible-example solution for the post-repair solve episode."""


def solve(grid):
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list of rows")
    if any(not isinstance(row, list) or len(row) != 7 for row in grid):
        raise ValueError("expected a rectangular input with seven columns")
    return [
        [2 if row[col] != 0 or row[col + 4] != 0 else 0 for col in range(3)]
        for row in grid
    ]
