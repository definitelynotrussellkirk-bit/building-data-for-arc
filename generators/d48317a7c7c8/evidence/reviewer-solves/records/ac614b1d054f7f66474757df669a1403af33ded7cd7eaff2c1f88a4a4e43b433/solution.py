def solve(grid):
    result = [list(row) for row in grid]
    if not grid or not grid[0]:
        return result
    height, width = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(height) for c in range(width)
                 if grid[r][c] == 4}
    while remaining:
        origin = min(remaining)
        remaining.remove(origin)
        cells = {origin}
        stack = [origin]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    cells.add(point)
                    stack.append(point)
        if len(cells) != 3:
            continue
        rows = sorted({r for r, _ in cells})
        cols = sorted({c for _, c in cells})
        if len(rows) == 1:
            positions = [(rows[0], cols[0] - 1), (rows[0], cols[-1] + 1)]
        elif len(cols) == 1:
            positions = [(rows[0] - 1, cols[0]), (rows[-1] + 1, cols[0])]
        else:
            continue
        for r, c in positions:
            if 0 <= r < height and 0 <= c < width and grid[r][c] == 0:
                result[r][c] = 8
    return result
