"""Visible-example solution for the post-repair count-comparison task."""


def solve(grid):
    """Fill each 2x2 body block by comparing its column/row header counts."""
    if len(grid) != 11 or any(len(row) != 11 for row in grid):
        raise ValueError("expected an 11x11 grid")

    starts = (3, 6, 9)
    top_counts = [
        sum(grid[row][col] == 1 for row in range(2) for col in range(col0, col0 + 2))
        for col0 in starts
    ]
    left_counts = [
        sum(grid[row][col] == 2 for row in range(row0, row0 + 2) for col in range(2))
        for row0 in starts
    ]

    output = [row[:] for row in grid]
    for row_index, row0 in enumerate(starts):
        for col_index, col0 in enumerate(starts):
            top = top_counts[col_index]
            left = left_counts[row_index]
            color = 4 if top > left else 3 if top < left else 8
            for row in range(row0, row0 + 2):
                for col in range(col0, col0 + 2):
                    output[row][col] = color
    return output
