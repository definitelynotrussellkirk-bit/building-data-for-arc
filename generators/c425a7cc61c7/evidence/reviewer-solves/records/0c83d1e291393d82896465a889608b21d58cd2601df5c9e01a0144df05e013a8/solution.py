"""Visible-only solution for the blind ARC episode."""


def solve(grid):
    """Extract the object matching the corner key and rotate it 90° clockwise."""
    key = grid[0][0]
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == key and (r, c) != (0, 0)
    ]
    if not cells:
        return []

    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)

    cropped = [
        [key if grid[r][c] == key else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]

    # Clockwise rotation: output row c is the reversed input column c.
    return [list(reversed(column)) for column in zip(*cropped)]
