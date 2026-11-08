from copy import deepcopy


def solve(grid):
    """Complete qualifying monochrome diagonals in every original 2x2 window."""
    if not grid:
        return []
    source = [list(row) for row in grid]
    out = deepcopy(source)
    h = len(source)
    w = len(source[0]) if h else 0

    for r in range(h - 1):
        for c in range(w - 1):
            top_left = source[r][c]
            top_right = source[r][c + 1]
            bottom_left = source[r + 1][c]
            bottom_right = source[r + 1][c + 1]

            # Equal nonzero cells on the main diagonal, with both other
            # corners empty, complete the square in that same colour.
            if (
                top_left != 0
                and top_left == bottom_right
                and top_right == 0
                and bottom_left == 0
            ):
                out[r][c + 1] = top_left
                out[r + 1][c] = top_left

            # Symmetric rule for the anti-diagonal.
            if (
                top_right != 0
                and top_right == bottom_left
                and top_left == 0
                and bottom_right == 0
            ):
                out[r][c] = top_right
                out[r + 1][c + 1] = top_right

    return out
