def solve(grid):
    """Recolor edge-connected 8-objects by increasing area and header order."""
    out = [list(row) for row in grid]
    colors = [cell for cell in grid[0] if cell != 0]
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if r > 0 and value == 8
    }
    objects = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack, cells = [start], []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        objects.append(cells)
    if len(objects) != len(colors):
        raise ValueError("Expected one header marker per object")
    for color, cells in zip(colors, sorted(objects, key=len)):
        for r, c in cells:
            out[r][c] = color
    return out
