def solve(grid):
    """Join exactly two matching diagonal endpoints through an empty input gap."""
    points_by_color = {}
    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color:
                points_by_color.setdefault(color, []).append((row_index, column_index))

    result = [row[:] for row in grid]
    for color, points in points_by_color.items():
        if len(points) != 2:
            continue
        (r0, c0), (r1, c1) = points
        distance = r1 - r0
        if distance < 2 or abs(c1 - c0) != distance:
            continue
        column_step = 1 if c1 > c0 else -1
        interior = [(r0 + offset, c0 + offset * column_step)
                    for offset in range(1, distance)]
        if any(grid[r][c] != 0 for r, c in interior):
            continue
        for r, c in interior:
            result[r][c] = color
    return result
