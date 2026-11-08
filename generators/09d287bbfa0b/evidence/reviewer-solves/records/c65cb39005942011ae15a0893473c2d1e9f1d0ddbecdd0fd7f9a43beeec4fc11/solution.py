from __future__ import annotations


def solve(grid):
    """Reflect every off-axis non-7 source through the full non-7 cross.

    Sources are read from the original input in row-major order.  Their three
    reflected cells are painted when in bounds, so later sources can overwrite
    values painted by earlier ones (including original source locations).
    """
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    height = len(grid)
    width = len(grid[0])
    cross_row = next(
        (row for row in range(height) if all(value != 7 for value in grid[row])),
        None,
    )
    cross_col = next(
        (
            col
            for col in range(width)
            if all(grid[row][col] != 7 for row in range(height))
        ),
        None,
    )
    output = [list(row) for row in grid]
    if cross_row is None or cross_col is None:
        return output

    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == 7 or row == cross_row or col == cross_col:
                continue
            reflected = (
                (row, 2 * cross_col - col),
                (2 * cross_row - row, col),
                (2 * cross_row - row, 2 * cross_col - col),
            )
            for target_row, target_col in reflected:
                if 0 <= target_row < height and 0 <= target_col < width:
                    output[target_row][target_col] = value

    return output
