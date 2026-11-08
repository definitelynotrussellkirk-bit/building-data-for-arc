"""Visible-example solution for the reviewer blind task.

The color-1 cells are the source stencil.  Every other nonzero cell is a
colored registration mark for a reflected copy of that stencil.
"""


def solve(grid):
    """Return the grid with each marker's reflected color-1 stencil painted.

    A marker aligned with a source row uses the row's leftmost color-1 cell as
    its registration point and reflects left/right.  A marker aligned with a
    source column uses the column's topmost color-1 cell and reflects up/down.
    When both alignments are possible, the shorter marker-to-registration
    displacement selects the intended axis.  Reflections are clipped to the
    grid, and markers are applied in reading order.
    """
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    result = [list(row) for row in grid]

    source = [
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, color in enumerate(row)
        if color == 1
    ]
    markers = [
        (row_index, column_index, color)
        for row_index, row in enumerate(grid)
        for column_index, color in enumerate(row)
        if color not in (0, 1)
    ]

    for marker_row, marker_column, marker_color in markers:
        row_columns = [column for row, column in source if row == marker_row]
        column_rows = [row for row, column in source if column == marker_column]

        candidates = []
        if row_columns:
            anchor_column = min(row_columns)
            candidates.append(
                (
                    abs(marker_column - anchor_column),
                    "horizontal",
                    marker_row,
                    anchor_column,
                )
            )
        if column_rows:
            anchor_row = min(column_rows)
            candidates.append(
                (
                    abs(marker_row - anchor_row),
                    "vertical",
                    anchor_row,
                    marker_column,
                )
            )

        if not candidates:
            # The visible task always aligns each marker with the stencil.  If
            # an unexpected marker appears, preserve it rather than guessing.
            continue

        _, orientation, anchor_row, anchor_column = min(candidates)

        for source_row, source_column in source:
            if orientation == "horizontal":
                target_row = source_row
                target_column = anchor_column + marker_column - source_column
            else:
                target_row = anchor_row + marker_row - source_row
                target_column = source_column

            if 0 <= target_row < height and 0 <= target_column < width:
                result[target_row][target_column] = marker_color

    return result
