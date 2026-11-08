"""Visible-example-only solution for blind task 0b8ba9bb3c63."""


def solve(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    azure = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    if not azure:
        return out

    row_extents: dict[int, tuple[int, int]] = {}
    col_extents: dict[int, tuple[int, int]] = {}
    for r, c in azure:
        if r in row_extents:
            lo, hi = row_extents[r]
            row_extents[r] = (min(lo, c), max(hi, c))
        else:
            row_extents[r] = (c, c)
        if c in col_extents:
            lo, hi = col_extents[c]
            col_extents[c] = (min(lo, r), max(hi, r))
        else:
            col_extents[c] = (r, r)

    # A ray traverses background/red (and any pre-existing yellow), but all
    # other nonzero colors are opaque blockers.
    traversable = {0, 2, 4}

    for r, (left, right) in row_extents.items():
        for c in range(left - 1, -1, -1):
            if grid[r][c] not in traversable:
                break
            out[r][c] = 4
        for c in range(right + 1, width):
            if grid[r][c] not in traversable:
                break
            out[r][c] = 4

    for c, (top, bottom) in col_extents.items():
        for r in range(top - 1, -1, -1):
            if grid[r][c] not in traversable:
                break
            out[r][c] = 4
        for r in range(bottom + 1, height):
            if grid[r][c] not in traversable:
                break
            out[r][c] = 4

    return out
