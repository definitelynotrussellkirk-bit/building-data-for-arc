"""Visible-only solution for blind task 019445e9b5a1."""


def solve(grid):
    """Recolor each row's nonzero cells with that row's leftmost color."""
    out = []
    for row in grid:
        color = next((value for value in row if value != 0), 0)
        out.append([color if value != 0 else 0 for value in row])
    return out
