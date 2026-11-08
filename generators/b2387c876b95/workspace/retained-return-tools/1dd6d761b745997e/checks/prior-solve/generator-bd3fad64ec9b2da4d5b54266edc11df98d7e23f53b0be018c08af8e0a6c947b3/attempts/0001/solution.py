"""Visible-example solution for b2387c876b95."""


def solve(grid):
    """Reflect only color-2 cells across the full color-5 divider as color 3."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    height = len(grid)
    width = len(grid[0])
    full_rows = [
        row for row in range(height)
        if all(grid[row][col] == 5 for col in range(width))
    ]
    full_cols = [
        col for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    if len(full_rows) + len(full_cols) != 1:
        raise ValueError("expected exactly one complete color-5 divider")

    output = [list(row) for row in grid]
    if full_cols:
        divider = full_cols[0]
        for row in range(height):
            for col in range(width):
                if grid[row][col] == 2:
                    mirror_col = 2 * divider - col
                    if 0 <= mirror_col < width:
                        output[row][mirror_col] = 3
    else:
        divider = full_rows[0]
        for row in range(height):
            for col in range(width):
                if grid[row][col] == 2:
                    mirror_row = 2 * divider - row
                    if 0 <= mirror_row < height:
                        output[mirror_row][col] = 3
    return output
