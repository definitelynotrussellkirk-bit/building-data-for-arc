from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Apply the color substitution legend stored in the top-left 2-row block.

    The first row of the contiguous nonzero prefix lists source colors; the
    second row lists their replacements.  The legend itself is erased, while
    all other cells are transformed simultaneously.  Colors not named in the
    source row are left unchanged.
    """
    if len(grid) < 2 or not grid[0]:
        return [row[:] for row in grid]

    legend_width = 0
    for value in grid[0]:
        if value == 0:
            break
        legend_width += 1

    if legend_width == 0 or len(grid[1]) < legend_width:
        return [row[:] for row in grid]

    substitutions = {
        grid[0][column]: grid[1][column]
        for column in range(legend_width)
    }

    result = []
    for row_index, row in enumerate(grid):
        result_row = []
        for column_index, value in enumerate(row):
            if row_index < 2 and column_index < legend_width:
                result_row.append(0)
            else:
                result_row.append(substitutions.get(value, value))
        result.append(result_row)
    return result
