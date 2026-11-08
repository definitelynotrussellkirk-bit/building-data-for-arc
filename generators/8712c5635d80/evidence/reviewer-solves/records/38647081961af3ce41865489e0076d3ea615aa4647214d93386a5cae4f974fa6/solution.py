"""Visible-example solution for ARC task 8712c5635d80."""


def solve(grid):
    """Copy the left-panel shape into the right frame using the frame color."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    separator_columns = [
        c for c in range(width) if all(grid[r][c] == 9 for r in range(height))
    ]
    if len(separator_columns) != 1:
        raise ValueError("expected exactly one full-height color-9 separator")
    separator = separator_columns[0]

    right_start = separator + 1
    panel_width = separator
    if width - right_start != panel_width:
        raise ValueError("expected equal-width panels around the separator")

    frame_colors = {
        grid[r][c]
        for r in range(height)
        for c in range(right_start, width)
        if grid[r][c] != 0
    }
    if len(frame_colors) != 1:
        raise ValueError("expected one nonzero frame color in the right panel")
    frame_color = next(iter(frame_colors))

    output = [row[:] for row in grid]
    for r in range(height):
        for c in range(panel_width):
            if grid[r][c] != 0:
                output[r][right_start + c] = frame_color
    return output
