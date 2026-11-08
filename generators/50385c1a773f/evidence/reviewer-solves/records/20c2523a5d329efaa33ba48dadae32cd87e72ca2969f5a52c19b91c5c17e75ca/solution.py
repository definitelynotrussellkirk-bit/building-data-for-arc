def solve(grid):
    """Trace the reflected beam inferred from the public examples."""
    out = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    sources = [(r, c) for r, row in enumerate(grid)
               for c, value in enumerate(row) if value == 2]
    if len(sources) != 1:
        raise ValueError("Expected one red source")
    r, c = sources[0]
    dr, dc = 0, 1
    visited = set()
    while True:
        r, c = r + dr, c + dc
        if not (0 <= r < height and 0 <= c < width):
            break
        state = (r, c, dr, dc)
        if state in visited:
            break
        visited.add(state)
        value = grid[r][c]
        if value == 0 or value == 8:
            out[r][c] = 8
        elif value == 3:
            dr, dc = -dc, -dr
        elif value == 4:
            dr, dc = dc, dr
        else:
            break
    return out
