def solve(grid):
    blue_cells = [(r, c) for r, row in enumerate(grid)
                  for c, value in enumerate(row) if value == 1]
    if not blue_cells:
        raise ValueError("Expected a blue panel")
    r0 = min(r for r, _ in blue_cells)
    r1 = max(r for r, _ in blue_cells)
    c0 = min(c for _, c in blue_cells)
    c1 = max(c for _, c in blue_cells)
    panel = [list(row[c0:c1 + 1]) for row in grid[r0:r1 + 1]]
    key = {(r, c): value for r, row in enumerate(grid)
           for c, value in enumerate(row)
           if value and not (r0 <= r <= r1 and c0 <= c <= c1)}
    if len(key) != 3:
        raise ValueError("Expected three external marker cells")
    top, bottom = min(r for r, _ in key), max(r for r, _ in key)
    left, right = min(c for _, c in key), max(c for _, c in key)
    target = tuple(key.get(point, 1) for point in
                   [(top, left), (top, right), (bottom, left), (bottom, right)])

    def clockwise(a):
        return [list(row) for row in zip(*a[::-1])]

    def corners(a):
        return a[1][1], a[1][-2], a[-2][1], a[-2][-2]

    candidates = []
    for _ in range(4):
        candidates.append(panel)
        candidates.append([row[::-1] for row in panel])
        panel = clockwise(panel)
    matches = [a for a in candidates if corners(a) == target]
    if len(matches) != 1:
        raise ValueError("The full corner pattern must identify one panel orientation")
    return [row[:] for row in matches[0]]
