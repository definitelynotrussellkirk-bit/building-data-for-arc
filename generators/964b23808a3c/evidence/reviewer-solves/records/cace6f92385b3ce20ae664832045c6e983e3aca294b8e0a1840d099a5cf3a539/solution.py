from copy import deepcopy


def solve(grid):
    """Fill selected marker columns in top-to-bottom color segments."""
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    out = deepcopy(grid)

    for col in range(width):
        markers = [
            (row, grid[row][col])
            for row in range(height)
            if grid[row][col] != 0
        ]
        # The examples select only columns whose final nonzero marker is 5.
        if not markers or markers[-1][1] != 5:
            continue

        previous_row = -1
        for marker_row, color in markers:
            # Each marker owns the interval immediately above it, including
            # its own cell.  The first marker therefore colors from row 0.
            for row in range(previous_row + 1, marker_row + 1):
                out[row][col] = color
            previous_row = marker_row

    return out
