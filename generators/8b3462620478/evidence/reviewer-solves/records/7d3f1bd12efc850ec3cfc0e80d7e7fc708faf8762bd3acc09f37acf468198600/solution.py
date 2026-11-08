from copy import deepcopy


def solve(grid):
    """Trace the beam encoded by colors 2/1 through mirrors 3/4."""
    out = deepcopy(grid)
    source = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    arrow = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]
    if len(source) != 1 or len(arrow) != 1:
        return out

    sr, sc = source[0]
    ar, ac = arrow[0]
    dr, dc = ar - sr, ac - sc
    if abs(dr) + abs(dc) != 1:
        return out

    rows, cols = len(grid), len(grid[0])
    r, c = ar + dr, ac + dc
    for _ in range(500):
        if not (0 <= r < rows and 0 <= c < cols) or grid[r][c] == 5:
            break
        value = grid[r][c]
        if value == 0:
            out[r][c] = 8
        elif value == 3:  # slash mirror
            dr, dc = -dc, -dr
        elif value == 4:  # backslash mirror
            dr, dc = dc, dr
        r, c = r + dr, c + dc
    return out
