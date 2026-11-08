from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Rotate every non-key, non-pivot colored cell around the color-9 pivot.

    The value in the upper-left corner encodes the number of clockwise
    quarter-turns as key - 1.  The key and pivot remain fixed and the source
    locations are cleared.
    """
    height = len(grid)
    width = len(grid[0])
    key = grid[0][0]
    pivots = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 9
    ]
    if len(pivots) != 1:
        raise ValueError(f"expected one color-9 pivot, found {len(pivots)}")
    pivot_row, pivot_col = pivots[0]

    output = [[0 for _ in range(width)] for _ in range(height)]
    output[0][0] = key
    output[pivot_row][pivot_col] = 9

    turns = (key - 1) % 4
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) == (0, 0) or color == 9:
                continue
            dr, dc = row - pivot_row, col - pivot_col
            for _ in range(turns):
                dr, dc = dc, -dr
            new_row, new_col = pivot_row + dr, pivot_col + dc
            if not (0 <= new_row < height and 0 <= new_col < width):
                raise ValueError("visible rule would rotate a cell out of bounds")
            output[new_row][new_col] = color
    return output
