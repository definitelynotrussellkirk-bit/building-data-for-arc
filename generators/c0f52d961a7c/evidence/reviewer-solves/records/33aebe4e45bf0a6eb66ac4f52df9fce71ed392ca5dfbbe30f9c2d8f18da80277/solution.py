"""Visible-example solution for task c0f52d961a7c."""

_DIRECTIONS = {
    1: (0, -1),   # left
    2: (-1, 0),   # up
    3: (0, 1),    # right
    4: (1, 0),    # down
}


def solve(grid):
    """Remove the direction marker and move the gray shape one cell."""
    if not grid or not grid[0]:
        raise ValueError("grid must be non-empty")

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    markers = [cell for row in grid for cell in row if cell in _DIRECTIONS]
    if len(markers) != 1:
        raise ValueError(f"expected exactly one direction marker, got {markers!r}")
    dr, dc = _DIRECTIONS[markers[0]]

    output = [[0 for _ in range(width)] for _ in range(height)]
    gray_cells = 0
    for row_index, row in enumerate(grid):
        for column_index, cell in enumerate(row):
            if cell != 6:
                continue
            target_row = row_index + dr
            target_column = column_index + dc
            if not (0 <= target_row < height and 0 <= target_column < width):
                raise ValueError("translated gray shape leaves the grid")
            output[target_row][target_column] = 6
            gray_cells += 1

    if gray_cells == 0:
        raise ValueError("expected at least one gray cell")
    return output
