from copy import deepcopy


def solve(grid):
    """Mirror the source object into all four divider quadrants.

    The horizontal and vertical divider lines are entirely color 9.  The
    original object keeps its color; every newly created reflected cell is 8.
    """
    if not grid or not grid[0]:
        return deepcopy(grid)

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    divider_rows = [r for r, row in enumerate(grid) if all(value == 9 for value in row)]
    divider_cols = [
        c for c in range(width) if all(grid[r][c] == 9 for r in range(height))
    ]
    if len(divider_rows) != 1 or len(divider_cols) != 1:
        raise ValueError("expected one full horizontal and one full vertical color-9 divider")

    divider_row = divider_rows[0]
    divider_col = divider_cols[0]
    source_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]

    result = deepcopy(grid)
    for row, col in source_cells:
        reflected_rows = {row, 2 * divider_row - row}
        reflected_cols = {col, 2 * divider_col - col}
        for target_row in reflected_rows:
            for target_col in reflected_cols:
                if not (0 <= target_row < height and 0 <= target_col < width):
                    raise ValueError("reflected object falls outside the grid")
                if target_row == row and target_col == col:
                    continue
                if result[target_row][target_col] == 0:
                    result[target_row][target_col] = 8

    return result
