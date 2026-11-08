"""Visible-example-only solution for the reviewer blind puzzle."""


def _rotate_clockwise(row_offset, col_offset, quarter_turns):
    """Rotate an offset clockwise by 0, 90, 180, or 270 degrees."""
    quarter_turns %= 4
    for _ in range(quarter_turns):
        row_offset, col_offset = col_offset, -row_offset
    return row_offset, col_offset


def solve(grid):
    """Stamp the 8-cell stencil around colored rotation markers.

    The unique 9 cell is the stencil origin.  Every 8 cell supplies one
    relative stencil offset.  Marker colors 2, 3, 4, and 5 select clockwise
    rotations of 0, 90, 180, and 270 degrees respectively; their stamped
    cells are colored 4, 5, 6, and 7.  Original marker cells are protected.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    origins = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 9
    ]
    if len(origins) != 1:
        raise ValueError("expected exactly one stencil origin (color 9)")
    origin_row, origin_col = origins[0]

    stencil = [
        (row - origin_row, col - origin_col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 8
    ]

    markers = [
        (grid[row][col], row, col)
        for row in range(height)
        for col in range(width)
        if 2 <= grid[row][col] <= 5
    ]
    marker_positions = {(row, col) for _, row, col in markers}

    output = [[0 for _ in range(width)] for _ in range(height)]
    for color, row, col in markers:
        output[row][col] = color

    # Ascending marker color reproduces the observed overlap priority: later,
    # higher-color stamps replace earlier stamps, while marker cells stay fixed.
    for marker_color, marker_row, marker_col in sorted(markers):
        turns = marker_color - 2
        paint_color = marker_color + 2
        for row_offset, col_offset in stencil:
            dr, dc = _rotate_clockwise(row_offset, col_offset, turns)
            target_row = marker_row + dr
            target_col = marker_col + dc
            if not (0 <= target_row < height and 0 <= target_col < width):
                continue
            if (target_row, target_col) in marker_positions:
                continue
            output[target_row][target_col] = paint_color

    return output
