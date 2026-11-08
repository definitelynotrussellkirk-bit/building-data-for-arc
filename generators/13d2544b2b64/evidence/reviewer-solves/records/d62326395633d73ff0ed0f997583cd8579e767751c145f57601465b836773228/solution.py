"""Complete matching endpoint marks across the three-by-three tile layout."""


def solve(grid):
    """Join equal endpoint colors through the middle tile, horizontally last."""
    result = [list(row) for row in grid]
    tile_origins = (0, 3, 6)

    # Vertical endpoint pairs fill the same position in the middle tile row.
    for column_origin in tile_origins:
        for local_row in range(2):
            for local_column in range(2):
                column = column_origin + local_column
                color = grid[local_row][column]
                if color not in (0, 1) and grid[6 + local_row][column] == color:
                    result[3 + local_row][column] = color

    # Horizontal completion takes priority at crossings. Both passes read the
    # original endpoints so inferred cells do not become new source evidence.
    for row_origin in tile_origins:
        for local_row in range(2):
            for local_column in range(2):
                row = row_origin + local_row
                color = grid[row][local_column]
                if color not in (0, 1) and grid[row][6 + local_column] == color:
                    result[row][3 + local_column] = color

    return result
