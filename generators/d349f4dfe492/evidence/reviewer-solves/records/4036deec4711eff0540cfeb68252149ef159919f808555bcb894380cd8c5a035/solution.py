from __future__ import annotations


def solve(grid):
    """Preserve each nonzero seed and paint its Manhattan-distance-2 shell."""
    source = [list(row) for row in grid]
    output = [row[:] for row in source]
    if not source or not source[0]:
        return output

    height = len(source)
    width = len(source[0])
    seeds = [
        (row, col, source[row][col])
        for row in range(height)
        for col in range(width)
        if source[row][col] != 0
    ]
    for row, col, color in seeds:
        for out_row in range(height):
            for out_col in range(width):
                if (
                    source[out_row][out_col] == 0
                    and output[out_row][out_col] == 0
                    and abs(out_row - row) + abs(out_col - col) == 2
                ):
                    output[out_row][out_col] = color
    return output
