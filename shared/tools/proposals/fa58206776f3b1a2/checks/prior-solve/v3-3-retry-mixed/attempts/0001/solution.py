def solve(grid):
    """Orient a whole blue panel to match its separate three-dot corner key."""
    blue = [(r, c) for r, row in enumerate(grid)
            for c, value in enumerate(row) if value == 1]
    if not blue:
        raise ValueError("No blue panel")
    top = min(r for r, _ in blue)
    bottom = max(r for r, _ in blue)
    left = min(c for _, c in blue)
    right = max(c for _, c in blue)
    panel = [row[left:right + 1] for row in grid[top:bottom + 1]]
    dots = {(r, c): value for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value != 0 and not (top <= r <= bottom and left <= c <= right)}
    if len(dots) != 3:
        raise ValueError("Expected three external key dots")
    r0, r1 = min(r for r, _ in dots), max(r for r, _ in dots)
    c0, c1 = min(c for _, c in dots), max(c for _, c in dots)
    desired = tuple(dots.get(point, 1) for point in
                    ((r0, c0), (r0, c1), (r1, c0), (r1, c1)))
    matches = []
    for _ in range(4):
        for candidate in (panel, [list(reversed(row)) for row in panel]):
            signature = (candidate[1][1], candidate[1][-2],
                         candidate[-2][1], candidate[-2][-2])
            if signature == desired:
                matches.append([row[:] for row in candidate])
        height, width = len(panel), len(panel[0])
        panel = [[panel[height - 1 - c][r] for c in range(height)]
                 for r in range(width)]
    if len(matches) != 1:
        raise ValueError("The corner key does not choose exactly one orientation")
    return matches[0]
