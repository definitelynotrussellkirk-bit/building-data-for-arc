"""Visible-only solution for the post-repair ARC challenge."""


def solve(grid):
    """Reflect the original blue shape toward each aligned colored marker.

    Markers are processed in row-major order.  A same-column blue anchor has
    priority; otherwise the first same-row blue anchor is used.  The blue shape
    is reflected across the midpoint between the marker and that anchor, clipped
    to the input bounds, and painted in the marker's color.
    """
    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]

    blue_cells = [
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column] == 1
    ]
    markers = [
        (row, column, grid[row][column])
        for row in range(height)
        for column in range(width)
        if grid[row][column] not in (0, 1)
    ]

    for marker_row, marker_column, marker_color in markers:
        column_anchor = next(
            (
                (row, column)
                for row, column in blue_cells
                if column == marker_column
            ),
            None,
        )
        if column_anchor is not None:
            anchor_row, _ = column_anchor
            for blue_row, blue_column in blue_cells:
                reflected_row = anchor_row + marker_row - blue_row
                if 0 <= reflected_row < height:
                    output[reflected_row][blue_column] = marker_color
            continue

        row_anchor = next(
            (
                (row, column)
                for row, column in blue_cells
                if row == marker_row
            ),
            None,
        )
        if row_anchor is None:
            continue

        _, anchor_column = row_anchor
        for blue_row, blue_column in blue_cells:
            reflected_column = anchor_column + marker_column - blue_column
            if 0 <= reflected_column < width:
                output[blue_row][reflected_column] = marker_color

    return output
