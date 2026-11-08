"""Inferred from the three visible examples only."""
def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('Expected a nonempty rectangular grid')
    remaining = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2}
    counts = {1: 0, 3: 0}
    while remaining:
        stack = [remaining.pop()]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for p in ((r-1,c), (r+1,c), (r,c-1), (r,c+1)):
                if p in remaining:
                    remaining.remove(p)
                    stack.append(p)
        top = min(r for r, c in cells)
        left = min(c for r, c in cells)
        shape = {(r-top, c-left) for r,c in cells}
        if shape == {(0,1), (1,0), (1,1), (1,2)}:
            counts[3] += 1
        elif shape == {(0,0), (0,1), (0,2), (1,1)}:
            counts[1] += 1
        else:
            raise ValueError('Unrecognized red component')
    out = [[0]*6 for _ in range(3)]
    corners = [(0,0), (2,0), (0,2), (2,2)]
    for color, offset in ((3,0), (1,3)):
        if counts[color] > 4:
            raise ValueError('Visible examples do not establish encoding above four')
        for r,c in corners[:counts[color]]:
            out[r][c+offset] = color
    return out
