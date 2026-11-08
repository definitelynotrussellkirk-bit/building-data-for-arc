from typing import Sequence


def solve(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Complete every 2x2 block containing exactly three cyan cells.

    Candidate windows are detected from the original input so newly filled
    cells cannot create cascading completions.
    """
    if not grid:
        return []

    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    original = [list(row) for row in grid]
    output = [row[:] for row in original]

    for row in range(len(original) - 1):
        for column in range(width - 1):
            cells = (
                (row, column),
                (row, column + 1),
                (row + 1, column),
                (row + 1, column + 1),
            )
            values = [original[r][c] for r, c in cells]
            if values.count(8) == 3 and values.count(0) == 1:
                missing_index = values.index(0)
                missing_row, missing_column = cells[missing_index]
                output[missing_row][missing_column] = 8

    return output
