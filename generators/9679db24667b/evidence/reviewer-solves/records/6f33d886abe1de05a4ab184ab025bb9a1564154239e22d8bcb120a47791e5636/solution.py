from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Resolve ambiguous gray (9) cells row by row.

    A row supplies a definite replacement exactly when all of its colored,
    non-background, non-gray cells have one common color.  In that case every
    9 in the row is recolored with that color.  Rows with no such color or with
    multiple candidate colors are left unchanged.
    """
    result = [row[:] for row in grid]
    for row in result:
        candidates = {cell for cell in row if cell not in (0, 9)}
        if len(candidates) == 1:
            (replacement,) = candidates
            for column, cell in enumerate(row):
                if cell == 9:
                    row[column] = replacement
    return result
