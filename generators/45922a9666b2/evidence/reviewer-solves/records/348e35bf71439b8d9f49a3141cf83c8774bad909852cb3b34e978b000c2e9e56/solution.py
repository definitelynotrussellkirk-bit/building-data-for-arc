from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Extend each bottom-row red marker upward, detouring right around gray.

    A path moves straight up through non-gray cells.  When the cell directly
    above is gray (5), it takes one horizontal step to the right on its current
    row, provided that cell exists and is not gray, then resumes moving upward.
    A path stops at the top edge or when neither move is possible.  Paths are
    traced against the original gray-obstacle layout and may overlap.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    result = [row[:] for row in grid]
    starts = [column for column, value in enumerate(grid[-1]) if value == 2]

    for start_column in starts:
        row = height - 1
        column = start_column
        visited: set[tuple[int, int]] = set()

        while (row, column) not in visited:
            visited.add((row, column))
            result[row][column] = 2

            if row == 0:
                break

            if grid[row - 1][column] != 5:
                row -= 1
            elif column + 1 < width and grid[row][column + 1] != 5:
                column += 1
            else:
                break

    return result
