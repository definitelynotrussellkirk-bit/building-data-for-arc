from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Extend every yellow (4) cell rightward with azure (8).

    The extension stops immediately before the first maroon (9) cell to the
    right, or at the row boundary when no maroon cell follows. Existing
    non-background cells are preserved; only zero cells on the ray become 8.
    """
    output = [row[:] for row in grid]

    for row_index, row in enumerate(grid):
        width = len(row)
        for start in (index for index, value in enumerate(row) if value == 4):
            stop = next(
                (index for index in range(start + 1, width) if row[index] == 9),
                width,
            )
            for column in range(start + 1, stop):
                if output[row_index][column] == 0:
                    output[row_index][column] = 8

    return output
