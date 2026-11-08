"""Visible-example solution for the blind ARC episode."""


def _rotate_clockwise(grid):
    return [list(row) for row in zip(*grid[::-1])]


def solve(grid):
    """Crop the payload and apply the header's quarter-turn code."""
    rows = len(grid)
    cols = len(grid[0]) if rows else 0

    # The examples place a compact instruction in the first row and the
    # payload below it.  Keep every non-background payload cell inside one
    # rectangular crop, including interior/background holes.
    payload = [
        (r, c)
        for r in range(1, rows)
        for c in range(cols)
        if grid[r][c] != 0
    ]
    if not payload:
        payload = [
            (r, c)
            for r in range(rows)
            for c in range(cols)
            if grid[r][c] != 0
        ]
    if not payload:
        return []

    r0 = min(r for r, _ in payload)
    r1 = max(r for r, _ in payload)
    c0 = min(c for _, c in payload)
    c1 = max(c for _, c in payload)
    out = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]

    # Observed code classes: 0 -> 0 turns, 3 -> 1 clockwise turn,
    # 5 -> 2 clockwise turns.  The parsimonious interpolation is floor(code/2).
    turns = (grid[0][0] // 2) % 4 if rows and cols else 0
    for _ in range(turns):
        out = _rotate_clockwise(out)
    return out
