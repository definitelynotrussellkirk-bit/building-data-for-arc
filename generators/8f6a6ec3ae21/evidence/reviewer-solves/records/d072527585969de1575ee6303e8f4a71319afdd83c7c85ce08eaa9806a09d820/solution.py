def solve(grid):
    """Project row/column edge markers into their intersections.

    Rows whose left-edge cell is 1 and columns whose top-edge cell is 2
    produce color 8 at their intersections.  All other cells are cleared.
    """
    if not grid:
        return []
    width = len(grid[0])
    row_markers = [row[0] == 1 for row in grid]
    col_markers = [value == 2 for value in grid[0]]
    return [
        [8 if row_markers[r] and col_markers[c] else 0 for c in range(width)]
        for r in range(len(grid))
    ]
