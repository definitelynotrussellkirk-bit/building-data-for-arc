"""Visible-example solution for the prepared ARC episode."""


def solve(grid):
    """Replace each row containing color 6 by an aligned color-8 bar.

    The bar has one cell for every non-background (non-7) input cell in
    the row.  Its alignment preserves the ordinal position of the 6 among
    those non-background cells: the cell corresponding to 6 stays in the
    same column.  Rows without a 6 become all background.
    """
    if not grid:
        return []

    width = len(grid[0])
    output = []
    for row in grid:
        result = [7] * width
        occupied = [column for column, value in enumerate(row) if value != 7]
        anchors = [column for column, value in enumerate(row) if value == 6]
        if anchors:
            anchor = anchors[0]
            anchor_rank = occupied.index(anchor)
            start = anchor - anchor_rank
            for column in range(start, start + len(occupied)):
                if 0 <= column < width:
                    result[column] = 8
        output.append(result)
    return output
