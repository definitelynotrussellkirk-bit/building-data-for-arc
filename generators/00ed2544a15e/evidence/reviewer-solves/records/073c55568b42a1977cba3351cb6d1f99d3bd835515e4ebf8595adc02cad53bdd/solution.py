from __future__ import annotations


def _clear_segment(grid, a, b):
    """Return the interior cells when two points share a clear row/column."""
    ar, ac = a
    br, bc = b
    if ar == br:
        step = 1 if bc > ac else -1
        cells = [(ar, c) for c in range(ac + step, bc, step)]
    elif ac == bc:
        step = 1 if br > ar else -1
        cells = [(r, ac) for r in range(ar + step, br, step)]
    else:
        return None
    return cells if all(grid[r][c] == 0 for r, c in cells) else None


def solve(grid):
    """Join the unique red hub to its three unobstructed axial red endpoints."""
    out = [row[:] for row in grid]
    red = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]

    candidates = []
    for hub in red:
        rays = []
        hr, hc = hub
        for direction in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            dr, dc = direction
            aligned = []
            for point in red:
                if point == hub:
                    continue
                pr, pc = point
                delta_r, delta_c = pr - hr, pc - hc
                if (dr and delta_c == 0 and delta_r * dr > 0) or (
                    dc and delta_r == 0 and delta_c * dc > 0
                ):
                    aligned.append((abs(delta_r) + abs(delta_c), point))
            if aligned:
                _, endpoint = min(aligned)
                cells = _clear_segment(grid, hub, endpoint)
                if cells is not None:
                    rays.append((endpoint, cells))
        candidates.append((len(rays), hub, rays))

    ray_count, _, rays = max(candidates, key=lambda item: item[0])
    if ray_count < 3:
        return out

    for _, cells in rays:
        for r, c in cells:
            out[r][c] = 8
    return out
