def solve(grid):
    """Fill a blue diamond around each red line, inferred from visible pairs."""
    out = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width)
              if grid[r][c] == 2}
    while unseen:
        start = unseen.pop()
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        vertical = min(cols) == max(cols)
        low = min(rows) if vertical else min(cols)
        high = max(rows) if vertical else max(cols)
        for r, c in component:
            along = r if vertical else c
            radius = min(along - low, high - along)
            for offset in range(-radius, radius + 1):
                rr, cc = (r, c + offset) if vertical else (r + offset, c)
                if 0 <= rr < height and 0 <= cc < width and grid[rr][cc] == 0:
                    out[rr][cc] = 8
    return out
