def solve(grid):
    """Translate the red shape to the outside of the cyan frame."""
    rows = [list(row) for row in grid]
    frame = [(r, c) for r, row in enumerate(rows) for c, x in enumerate(row) if x == 8]
    moving = [(r, c) for r, row in enumerate(rows) for c, x in enumerate(row) if x == 2]
    if not frame or not moving:
        return rows
    fr0, fr1 = min(r for r, _ in frame), max(r for r, _ in frame)
    fc0, fc1 = min(c for _, c in frame), max(c for _, c in frame)
    mr0, mr1 = min(r for r, _ in moving), max(r for r, _ in moving)
    mc0, mc1 = min(c for _, c in moving), max(c for _, c in moving)
    dr = dc = 0
    if mr1 < fr0:
        dr = fr0 - mr1 - 1
    elif mr0 > fr1:
        dr = fr1 + 1 - mr0
    elif mc1 < fc0:
        dc = fc0 - mc1 - 1
    elif mc0 > fc1:
        dc = fc1 + 1 - mc0
    for r, c in moving:
        rows[r][c] = 0
    for r, c in moving:
        rows[r + dr][c + dc] = 2
    return rows
