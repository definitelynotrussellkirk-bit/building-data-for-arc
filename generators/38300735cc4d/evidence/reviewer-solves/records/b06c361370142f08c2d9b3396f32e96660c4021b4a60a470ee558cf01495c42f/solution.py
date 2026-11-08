def solve(grid):
    """Join isolated equal-color pairs along clear horizontal/vertical spans."""
    result = [list(row) for row in grid]
    positions = {}
    for row, values in enumerate(grid):
        for column, color in enumerate(values):
            if color != 0:
                positions.setdefault(color, []).append((row, column))

    for color, points in positions.items():
        if len(points) != 2:
            continue
        (r1, c1), (r2, c2) = points
        if r1 == r2:
            interior = [(r1, c) for c in range(min(c1, c2) + 1, max(c1, c2))]
        elif c1 == c2:
            interior = [(r, c1) for r in range(min(r1, r2) + 1, max(r1, r2))]
        else:
            continue
        if all(grid[r][c] == 0 for r, c in interior):
            for r, c in interior:
                result[r][c] = color
    return result
