from __future__ import annotations


def solve(grid):
    """Stretch the sparse color-3 lattice to boundaries named by color-6 markers."""
    height = len(grid)
    width = len(grid[0])

    lattice = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == 3
    ]
    if not lattice:
        return [row[:] for row in grid]

    r0 = min(row for row, _ in lattice)
    r1 = max(row for row, _ in lattice)
    c0 = min(column for _, column in lattice)
    c1 = max(column for _, column in lattice)

    full_rows = [
        row
        for row in range(r0, r1 + 1)
        if all(grid[row][column] == 3 for column in range(c0, c1 + 1))
    ]
    full_columns = [
        column
        for column in range(c0, c1 + 1)
        if all(grid[row][column] == 3 for row in range(r0, r1 + 1))
    ]
    markers = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == 6
    ]

    top = [row for row, column in markers if row < r0 and c0 <= column <= c1]
    bottom = [row for row, column in markers if row > r1 and c0 <= column <= c1]
    left = [column for row, column in markers if column < c0]
    right = [column for row, column in markers if column > c1]

    new_r0 = max(top) + 1 if top else r0
    new_r1 = min(bottom) - 1 if bottom else r1
    new_c0 = max(left) + 1 if left else c0
    new_c1 = min(right) - 1 if right else c1

    output = [[0 for _ in range(width)] for _ in range(height)]

    for row in full_rows:
        target_row = new_r0 if row == r0 else new_r1 if row == r1 else row
        for column in range(new_c0, new_c1 + 1):
            output[target_row][column] = 3

    for column in full_columns:
        target_column = new_c0 if column == c0 else new_c1 if column == c1 else column
        for row in range(new_r0, new_r1 + 1):
            output[row][target_column] = 3

    # Marker cells are clues and remain unchanged, even if a line reaches them.
    for row, column in markers:
        output[row][column] = 6

    return output
