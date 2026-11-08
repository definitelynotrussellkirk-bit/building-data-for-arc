"""Visible-example-only solver for blind task c0f52d961a7c."""

_DIRECTIONS = {
    1: (0, -1),   # left
    2: (-1, 0),   # up
    3: (0, 1),    # right
    4: (1, 0),    # down
}


def solve(grid):
    """Remove the colored direction marker and move the gray object one cell."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    marker_colors = {
        value
        for row in grid
        for value in row
        if value in _DIRECTIONS
    }
    if len(marker_colors) != 1:
        raise ValueError(f"expected exactly one direction-marker color, got {sorted(marker_colors)}")

    dr, dc = _DIRECTIONS[next(iter(marker_colors))]
    result = [[0 for _ in range(width)] for _ in range(height)]

    for r, row in enumerate(grid):
        if len(row) != width:
            raise ValueError("grid must be rectangular")
        for c, value in enumerate(row):
            if value != 6:
                continue
            nr, nc = r + dr, c + dc
            if not (0 <= nr < height and 0 <= nc < width):
                raise ValueError("shifted gray object would leave the grid")
            result[nr][nc] = 6

    return result
