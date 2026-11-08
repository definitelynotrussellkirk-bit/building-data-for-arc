from collections import Counter, deque


def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _convex_hull(points):
    points = sorted(set(points))
    if len(points) <= 1:
        return points

    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and _cross(out[-2], out[-1], p) <= 0:
                out.pop()
            out.append(p)
        return out

    lower = half(points)
    upper = half(reversed(points))
    return lower[:-1] + upper[:-1]


def _inside(row, col, hull):
    inside = False
    j = len(hull) - 1
    for i, (ri, ci) in enumerate(hull):
        rj, cj = hull[j]
        if (ci > col) != (cj > col):
            crossing_row = ri + (rj - ri) * (col - ci) / (cj - ci)
            if row < crossing_row:
                inside = not inside
        j = i
    return inside


def _hull_cells(cells):
    cells = tuple(cells)
    if len(cells) < 3:
        return set()
    corners = []
    for r, c in cells:
        corners.extend(((r - 0.5, c - 0.5), (r - 0.5, c + 0.5),
                        (r + 0.5, c - 0.5), (r + 0.5, c + 0.5)))
    hull = _convex_hull(corners)
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
            if _inside(r, c, hull)}


def _components(grid, color):
    remaining = {(r, c) for r, row in enumerate(grid)
                 for c, value in enumerate(row) if value == color}
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        q = deque([start])
        component = set()
        while q:
            r, c = q.popleft()
            component.add((r, c))
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == dc == 0:
                        continue
                    p = (r + dr, c + dc)
                    if p in remaining:
                        remaining.remove(p)
                        q.append(p)
        result.append(component)
    return result


def solve(grid):
    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]
    colors = [color for color in counts if color != background]

    matches = []
    for target in colors:
        donor = next(color for color in colors if color != target)
        donor_cells = {(r, c) for r, row in enumerate(grid)
                       for c, value in enumerate(row) if value == donor}
        for component in _components(grid, target):
            missing = {p for p in _hull_cells(component)
                       if grid[p[0]][p[1]] == background}
            if missing and len(missing) == len(donor_cells):
                matches.append((donor, donor_cells, missing))

    if len(matches) != 1:
        raise ValueError(f"expected one count-matching hull, found {len(matches)}")

    donor, donor_cells, missing = matches[0]
    output = [row[:] for row in grid]
    for r, c in donor_cells:
        output[r][c] = background
    for r, c in missing:
        output[r][c] = donor
    return output
