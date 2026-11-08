from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Copy the cyan support as an edge-adjacent horizontal reflection.

    The five yellow cells form a horizontal arrow.  Its single top-row apex is
    one column left or right of the three-cell bar's centre and selects the side
    on which the reflected cyan copy is painted.  The input is preserved.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    yellow = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 4]
    cyan = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    if not yellow or not cyan:
        return [row[:] for row in grid]

    top_row = min(r for r, _ in yellow)
    apex_columns = [c for r, c in yellow if r == top_row]
    if len(apex_columns) != 1:
        raise ValueError("expected one yellow arrow apex on the top yellow row")
    bar_row = top_row + 1
    bar_columns = sorted(c for r, c in yellow if r == bar_row)
    if len(bar_columns) != 3:
        raise ValueError("expected a three-cell yellow arrow bar")
    center = bar_columns[1]
    direction = 1 if apex_columns[0] > center else -1

    left = min(c for _, c in cyan)
    right = max(c for _, c in cyan)
    output = [row[:] for row in grid]
    for row, column in cyan:
        target = 2 * right + 1 - column if direction == 1 else 2 * left - 1 - column
        if not 0 <= target < width:
            raise ValueError("reflected cyan copy falls outside the grid")
        output[row][target] = 8
    return output
