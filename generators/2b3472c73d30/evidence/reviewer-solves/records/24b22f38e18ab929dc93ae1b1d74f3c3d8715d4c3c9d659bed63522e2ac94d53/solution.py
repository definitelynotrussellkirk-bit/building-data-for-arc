"""Blind solution derived only from solve-blind/challenge.json."""


def solve(grid):
    """Fill the horizontal span of rows containing exactly two equal markers.

    Rows with zero/one marker, mixed colors, or more than two nonzero cells are
    deliberately left unchanged, matching the visible counterexamples.
    """
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        nonzero = [(c, value) for c, value in enumerate(row) if value != 0]
        if len(nonzero) != 2:
            continue
        (left, color_left), (right, color_right) = nonzero
        if color_left != color_right:
            continue
        for c in range(left, right + 1):
            out[r][c] = color_left
    return out
