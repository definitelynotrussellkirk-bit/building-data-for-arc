"""Visible-only solution for blind task 9ce2dcf587b8."""


def solve(grid):
    """Draw both complete diagonals through every nonzero seed cell."""
    seeds = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not seeds:
        return [row[:] for row in grid]

    colors = {value for _, _, value in seeds}
    if len(colors) != 1:
        raise ValueError(f"expected one foreground color, found {sorted(colors)}")
    color = seeds[0][2]

    output = [row[:] for row in grid]
    for r, row in enumerate(output):
        for c in range(len(row)):
            if any(abs(r - sr) == abs(c - sc) for sr, sc, _ in seeds):
                row[c] = color
    return output
