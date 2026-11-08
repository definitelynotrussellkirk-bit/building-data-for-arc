"""Visible-example-only solver for the prepared ARC episode."""


def _shape(grid):
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        raise ValueError("grid must be a non-empty list of rows")
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    return len(grid), width


def solve(grid):
    """Fill each chamber using its dot count as a one-based legend index."""
    height, width = _shape(grid)
    if height < 4 or width < 7:
        raise ValueError("grid is too small for the demonstrated layout")

    legend = list(grid[0][1:4])
    if len(legend) != 3:
        raise ValueError("expected three legend entries")

    # Detect separators only in the framed body, so a legend entry equal to 8
    # cannot be mistaken for a wall.
    wall_columns = [
        col for col in range(width)
        if all(grid[row][col] == 8 for row in range(1, height))
    ]
    if len(wall_columns) != 4 or wall_columns[0] != 0 or wall_columns[-1] != width - 1:
        raise ValueError(f"expected four body wall columns, got {wall_columns}")

    wall_rows = [
        row for row in range(1, height)
        if all(value == 8 for value in grid[row])
    ]
    if len(wall_rows) < 2:
        raise ValueError("expected top and bottom horizontal walls")
    top_wall, bottom_wall = wall_rows[0], wall_rows[-1]
    if top_wall + 1 >= bottom_wall:
        raise ValueError("chamber interior is empty")

    output = [list(row) for row in grid]
    for left_wall, right_wall in zip(wall_columns, wall_columns[1:]):
        dots = sum(
            grid[row][col] == 1
            for row in range(top_wall + 1, bottom_wall)
            for col in range(left_wall + 1, right_wall)
        )
        if dots not in (1, 2, 3):
            raise ValueError(f"demonstrated mapping is defined for 1..3 dots, got {dots}")
        fill = legend[dots - 1]
        for row in range(top_wall + 1, bottom_wall):
            for col in range(left_wall + 1, right_wall):
                output[row][col] = fill
    return output
