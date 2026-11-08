def solve(grid):
    """Fill the 8-defined bounding box by nearest seed color."""
    out = [row[:] for row in grid]
    eights = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    if not eights:
        return out

    top = min(r for r, _ in eights)
    left = min(c for _, c in eights)
    bottom = max(r for r, _ in eights)
    right = max(c for _, c in eights)
    seeds = [
        (r, c, grid[r][c])
        for r in range(top + 1, bottom)
        for c in range(left + 1, right)
        if grid[r][c] not in (0, 8)
    ]
    if not seeds:
        return out

    for r in range(top + 1, bottom):
        for c in range(left + 1, right):
            distances = [abs(r - sr) + abs(c - sc) for sr, sc, _ in seeds]
            nearest_distance = min(distances)
            nearest_colors = {
                color
                for (sr, sc, color), distance in zip(seeds, distances)
                if distance == nearest_distance
            }
            out[r][c] = next(iter(nearest_colors)) if len(nearest_colors) == 1 else 0
    return out
