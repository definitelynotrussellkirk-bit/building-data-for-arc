"""Visible-example solution for the blind ARC episode."""


def solve(grid):
    """Fill one-cell horizontal gaps between equal nonzero markers.

    The visible examples consistently turn ``c, 0, c`` into ``c, c, c``.
    Applying the rule pairwise also fills longer alternating marker runs such as
    ``c, 0, c, 0, c`` while leaving larger gaps and vertical alignments alone.
    """
    out = [row[:] for row in grid]
    for row in out:
        for col in range(1, len(row) - 1):
            left = row[col - 1]
            if left != 0 and row[col] == 0 and row[col + 1] == left:
                row[col] = left
    return out
