"""Visible-example solution for blind task 3bb94038f4e2."""


def solve(grid):
    """Fill horizontal alternating 1-0-1-...-1 runs of length >= 5.

    A row is changed only when it contains at least three 1-cells whose
    consecutive column gaps are all exactly two.  The cells from the first to
    the last marker are then painted 1.  Other colors and all other rows are
    preserved.
    """
    output = [row[:] for row in grid]

    for r, row in enumerate(grid):
        one_columns = [c for c, value in enumerate(row) if value == 1]
        if len(one_columns) < 3:
            continue

        # Treat each maximal arithmetic run separately so an unrelated 1 in
        # the same row cannot cause the wrong span to be filled.
        start = 0
        while start < len(one_columns):
            end = start
            while (
                end + 1 < len(one_columns)
                and one_columns[end + 1] - one_columns[end] == 2
            ):
                end += 1

            if end - start + 1 >= 3:
                left = one_columns[start]
                right = one_columns[end]
                for c in range(left, right + 1):
                    output[r][c] = 1

            start = end + 1

    return output
