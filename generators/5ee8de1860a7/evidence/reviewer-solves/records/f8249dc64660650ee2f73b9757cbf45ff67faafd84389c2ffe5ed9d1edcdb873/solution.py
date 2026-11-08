"""Visible-example solution for blind task 5ee8de1860a7."""


def solve(grid):
    """Replace the lone colored marker with a frame of the same color."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    if height == 0 or width == 0:
        return []

    marker_colors = {cell for row in grid for cell in row if cell != 0}
    if len(marker_colors) != 1:
        raise ValueError(f"expected exactly one non-background color, got {marker_colors}")
    color = next(iter(marker_colors))

    return [
        [
            color if row in (0, height - 1) or col in (0, width - 1) else 0
            for col in range(width)
        ]
        for row in range(height)
    ]
