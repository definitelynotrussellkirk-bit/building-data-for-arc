from __future__ import annotations


def solve(grid):
    """Project yellow rays through the straight opening in an orthogonal wall."""
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    foreground = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    if not foreground:
        return out

    steps4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

    def add(a, b):
        return a[0] + b[0], a[1] + b[1]

    def neg(a):
        return -a[0], -a[1]

    def in_bounds(p):
        return 0 <= p[0] < h and 0 <= p[1] < w

    def paint_ray(start, delta):
        p = start
        while in_bounds(p) and p not in foreground:
            out[p[0]][p[1]] = 4
            p = add(p, delta)

    endpoints = []
    neighbor_dir = {}
    for p in foreground:
        neighbors = []
        for d in steps4:
            q = add(p, d)
            if q in foreground:
                neighbors.append(d)
        if len(neighbors) == 1:
            endpoints.append(p)
            neighbor_dir[p] = neighbors[0]

    if len(endpoints) != 2:
        return out

    a, b = endpoints
    if a[0] == b[0]:
        if a[1] > b[1]:
            a, b = b, a
        axis = (0, 1)
        normals = ((-1, 0), (1, 0))
        segment = [(a[0], c) for c in range(a[1], b[1] + 1)]
    elif a[1] == b[1]:
        if a[0] > b[0]:
            a, b = b, a
        axis = (1, 0)
        normals = ((0, -1), (0, 1))
        segment = [(r, a[1]) for r in range(a[0], b[0] + 1)]
    else:
        return out

    # Directions from each endpoint into the opening.
    gap_dir = {a: axis, b: neg(axis)}
    pa, pb = neighbor_dir[a], neighbor_dir[b]
    ga, gb = gap_dir[a], gap_dir[b]
    collinear = pa == neg(ga) and pb == neg(gb)
    perpendicular = (
        pa[0] * ga[0] + pa[1] * ga[1] == 0
        and pb[0] * gb[0] + pb[1] * gb[1] == 0
    )

    def project_straight(points):
        for p in points:
            for n in normals:
                paint_ray(add(p, n), n)

    if collinear:
        # The empty opening itself projects straight.  At its two ends, the
        # edge ray first leaves normally and then follows the outward arm at
        # 45 degrees, stopping at a wall or the grid edge.
        project_straight(segment[1:-1])
        for e in (a, b):
            pdir = neighbor_dir[e]
            for n in normals:
                first = add(e, n)
                if not in_bounds(first) or first in foreground:
                    continue
                out[first[0]][first[1]] = 4
                paint_ray(add(first, add(n, pdir)), add(n, pdir))
    elif perpendicular:
        # A C-shaped wall: project the open span straight, then chamfer the
        # two exposed corners on the side opposite the incident wall.
        project_straight(segment[1:-1])
        for e in (a, b):
            pdir = neighbor_dir[e]
            n = neg(pdir)
            first = add(e, n)
            if not in_bounds(first) or first in foreground:
                continue
            out[first[0]][first[1]] = 4
            delta = add(n, neg(gap_dir[e]))
            paint_ray(add(first, delta), delta)
    else:
        # Mixed straight/corner endpoint geometry: the whole mouth segment,
        # including its colored end cells, projects normally.
        project_straight(segment)

    return out
