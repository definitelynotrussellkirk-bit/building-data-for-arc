def solve(grid):
    """Compress nested solid rectangles into one-cell concentric square rings."""
    if not grid or not grid[0]:
        return []

    current = [row[:] for row in grid]
    layers = []

    while current:
        outer = current[0][0]
        layers.append(outer)

        different = [
            (r, c)
            for r, row in enumerate(current)
            for c, value in enumerate(row)
            if value != outer
        ]
        if not different:
            break

        rows = [r for r, _ in different]
        cols = [c for _, c in different]
        r0, r1 = min(rows), max(rows)
        c0, c1 = min(cols), max(cols)
        current = [row[c0 : c1 + 1] for row in current[r0 : r1 + 1]]

    size = 2 * len(layers) - 1
    result = [[layers[0] for _ in range(size)] for _ in range(size)]
    for depth, color in enumerate(layers[1:], start=1):
        for r in range(depth, size - depth):
            for c in range(depth, size - depth):
                result[r][c] = color
    return result
