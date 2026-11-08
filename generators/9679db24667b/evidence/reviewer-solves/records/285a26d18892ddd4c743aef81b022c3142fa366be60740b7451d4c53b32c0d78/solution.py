from __future__ import annotations


def solve(grid):
    """Replace each row's 9s only when that row has one distinct other color."""
    output = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        companion_colors = {value for value in row if value not in (0, 9)}
        if len(companion_colors) == 1 and 9 in row:
            replacement = next(iter(companion_colors))
            output[row_index] = [
                replacement if value == 9 else value
                for value in row
            ]
    return output
