"""Visible-example solution for blind task d8b498586958."""


def solve(grid):
    n = len(grid[0])
    upper = grid[3 : 3 + n]
    lower = grid[4 + n : 4 + 2 * n]

    marker = next(
        (r, c)
        for r in range(2)
        for c in range(n)
        if grid[r][c] == 5
    )

    # The four marker corners select the four demonstrated set operations.
    if marker == (0, 0):
        predicate = lambda a, b: a or b          # union / OR
    elif marker == (0, n - 1):
        predicate = lambda a, b: a and b         # intersection / AND
    elif marker == (1, 0):
        predicate = lambda a, b: bool(a) ^ bool(b)  # symmetric difference / XOR
    elif marker == (1, n - 1):
        predicate = lambda a, b: a and not b      # upper-only difference
    else:
        raise ValueError(f"unsupported marker position: {marker}")

    return [
        [8 if predicate(upper[r][c] == 2, lower[r][c] in (6, 7)) else 0 for c in range(n)]
        for r in range(n)
    ]
