"""Visible-only solution for the assigned ARC task."""


def solve(grid):
    out = [row[:] for row in grid]

    walls = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 7
    ]
    if not walls:
        return out

    r0 = min(r for r, _ in walls)
    r1 = max(r for r, _ in walls)
    c0 = min(c for _, c in walls)
    c1 = max(c for _, c in walls)

    seeds = [
        (r, c, grid[r][c])
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
        if grid[r][c] not in (0, 7)
    ]
    if not seeds:
        return out

    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            if grid[r][c] != 0:
                continue
            _, color = min(
                ((abs(r - sr) + abs(c - sc), color) for sr, sc, color in seeds),
                key=lambda item: (item[0], item[1]),
            )
            out[r][c] = color

    return out
