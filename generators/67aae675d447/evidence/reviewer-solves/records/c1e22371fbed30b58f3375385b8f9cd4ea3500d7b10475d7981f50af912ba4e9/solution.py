"""Visible-example solution for the post-repair challenge."""
from __future__ import annotations


def _only_position(grid, color):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]
    if len(cells) != 1:
        raise ValueError(f"expected exactly one cell of color {color}, got {len(cells)}")
    return cells[0]


def _delta(a, b):
    """Vector a -> b."""
    return b[0] - a[0], b[1] - a[1]


def solve(grid):
    """Transfer the source-local color-8 bounding box to the target frame.

    Colors 2/3/4 define the source origin and two ordered cardinal basis
    directions.  Colors 5/6/7 define the corresponding target frame.  The
    source motif is the color-8 cells in the 7x7 neighborhood centered at 2;
    color-8 cells farther away are distractors.  Paint the perimeter of the
    motif's axis-aligned bounding box in target-local coordinates.
    """
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("expected a nonempty rectangular grid")

    source = _only_position(grid, 2)
    source_u = _delta(source, _only_position(grid, 3))
    source_v = _delta(source, _only_position(grid, 4))
    target = _only_position(grid, 5)
    target_u = _delta(target, _only_position(grid, 6))
    target_v = _delta(target, _only_position(grid, 7))

    def cardinal_pair(u, v):
        return (
            abs(u[0]) + abs(u[1]) == 1
            and abs(v[0]) + abs(v[1]) == 1
            and u[0] * v[0] + u[1] * v[1] == 0
        )

    if not cardinal_pair(source_u, source_v) or not cardinal_pair(target_u, target_v):
        raise ValueError("frame markers must define ordered orthogonal cardinal bases")

    motif_local = []
    sr, sc = source
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 8:
                continue
            dr, dc = r - sr, c - sc
            # Cardinal orthonormal projection into the ordered source frame.
            u = dr * source_u[0] + dc * source_u[1]
            v = dr * source_v[0] + dc * source_v[1]
            if max(abs(u), abs(v)) <= 3:
                motif_local.append((u, v))

    if not motif_local:
        raise ValueError("source frame has no local color-8 motif")

    u_min = min(u for u, _ in motif_local)
    u_max = max(u for u, _ in motif_local)
    v_min = min(v for _, v in motif_local)
    v_max = max(v for _, v in motif_local)

    out = [list(row) for row in grid]
    tr, tc = target
    h, w = len(out), len(out[0])
    for u in range(u_min, u_max + 1):
        for v in range(v_min, v_max + 1):
            if u not in (u_min, u_max) and v not in (v_min, v_max):
                continue
            r = tr + u * target_u[0] + v * target_v[0]
            c = tc + u * target_u[1] + v * target_v[1]
            if not (0 <= r < h and 0 <= c < w):
                raise ValueError("transferred bounding box leaves the grid")
            out[r][c] = 8
    return out
