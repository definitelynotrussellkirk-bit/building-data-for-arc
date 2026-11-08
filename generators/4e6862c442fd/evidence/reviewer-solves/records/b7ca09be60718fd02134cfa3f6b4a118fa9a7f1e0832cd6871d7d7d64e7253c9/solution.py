from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Copy the color-8 motif from the 2/3/4 frame into the 5/6/7 frame."""
    out = [row[:] for row in grid]

    positions: dict[int, tuple[int, int]] = {}
    motif: list[tuple[int, int]] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (2, 3, 4, 5, 6, 7):
                positions[value] = (r, c)
            elif value == 8:
                motif.append((r, c))

    source_origin = positions[2]
    source_u = (
        positions[3][0] - source_origin[0],
        positions[3][1] - source_origin[1],
    )
    source_v = (
        positions[4][0] - source_origin[0],
        positions[4][1] - source_origin[1],
    )
    target_origin = positions[5]
    target_u = (
        positions[6][0] - target_origin[0],
        positions[6][1] - target_origin[1],
    )
    target_v = (
        positions[7][0] - target_origin[0],
        positions[7][1] - target_origin[1],
    )

    for r, c in motif:
        dr = r - source_origin[0]
        dc = c - source_origin[1]
        # Each source basis vector is a signed cardinal unit vector, so dot
        # products recover the signed local coordinates exactly.
        u = dr * source_u[0] + dc * source_u[1]
        v = dr * source_v[0] + dc * source_v[1]
        rr = target_origin[0] + u * target_u[0] + v * target_v[0]
        cc = target_origin[1] + u * target_u[1] + v * target_v[1]
        out[rr][cc] = 8

    return out
