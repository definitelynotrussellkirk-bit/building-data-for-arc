from typing import List

Grid = List[List[int]]


def _target_start(
    red_lo: int,
    red_hi: int,
    blue_lo: int,
    blue_hi: int,
) -> int:
    """Move one red bounding-box axis next to the blue one.

    The red extent stays immediately outside the nearest blue edge while
    preserving which side of the blue object it originally occupied.
    """
    span = red_hi - red_lo + 1
    if red_hi < blue_lo:  # red is before blue on this axis
        return blue_lo - span
    if red_lo > blue_hi:  # red is after blue on this axis
        return blue_hi + 1
    return red_lo


def solve(grid: Grid) -> Grid:
    red = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    blue = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 8]
    if not red or not blue:
        return [row[:] for row in grid]

    rr0 = min(r for r, _ in red)
    rr1 = max(r for r, _ in red)
    rc0 = min(c for _, c in red)
    rc1 = max(c for _, c in red)
    br0 = min(r for r, _ in blue)
    br1 = max(r for r, _ in blue)
    bc0 = min(c for _, c in blue)
    bc1 = max(c for _, c in blue)

    new_r0 = _target_start(rr0, rr1, br0, br1)
    new_c0 = _target_start(rc0, rc1, bc0, bc1)
    dr = new_r0 - rr0
    dc = new_c0 - rc0

    out = [row[:] for row in grid]
    for r, c in red:
        out[r][c] = 0
    for r, c in red:
        nr, nc = r + dr, c + dc
        if not (0 <= nr < len(out) and 0 <= nc < len(out[nr])):
            raise ValueError("translated red object leaves the grid")
        out[nr][nc] = 2
    return out
