def solve(grid):
    """Recolor each 4-connected nonzero object touching a 1-cell to color 4."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]
    seen = set()
    one_cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    }

    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color in (0, 1) or (r, c) in seen:
                continue

            component = []
            stack = [(r, c)]
            seen.add((r, c))
            touches_one = False

            while stack:
                cr, cc = stack.pop()
                component.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (nr, nc) in one_cells:
                        touches_one = True
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            if touches_one:
                for cr, cc in component:
                    out[cr][cc] = 4

    return out
