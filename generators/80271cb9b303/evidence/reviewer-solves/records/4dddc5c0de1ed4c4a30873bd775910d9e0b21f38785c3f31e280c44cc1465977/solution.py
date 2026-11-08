from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Extend each non-empty row's shortest visible left-anchored period."""
    output = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        nonzero = [column for column, value in enumerate(row) if value != 0]
        if not nonzero:
            continue
        right = nonzero[-1]
        period = None
        for candidate in range(1, right + 2):
            if all(row[column] == row[column % candidate] for column in range(right + 1)):
                period = candidate
                break
        if period is not None:
            output[row_index] = [row[column % period] for column in range(len(row))]
    return output
