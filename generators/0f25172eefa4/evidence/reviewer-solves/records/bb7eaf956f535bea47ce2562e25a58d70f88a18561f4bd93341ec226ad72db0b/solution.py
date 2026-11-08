"""Visible-example solution: read bottom-row instructions and arrange tiles."""

def solve(grid):
    body = [list(row) for row in grid[:-1]]
    points = [(r, c) for r, row in enumerate(body) for c, value in enumerate(row) if value]
    if not points:
        return [[]]
    r0 = min(r for r, c in points)
    r1 = max(r for r, c in points)
    c0 = min(c for r, c in points)
    c1 = max(c for r, c in points)
    motif = [row[c0:c1 + 1] for row in body[r0:r1 + 1]]
    tiles = []
    for token in grid[-1]:
        if token == 0:
            continue
        tile = [row[:] for row in motif]
        turns = {3: 1, 4: 2}.get(token, 0)
        for _ in range(turns):
            tile = [list(row) for row in zip(*tile[::-1])]
        tiles.append(tile)
    height = max(len(tile) for tile in tiles)
    out = [[] for _ in range(height)]
    for index, tile in enumerate(tiles):
        width = len(tile[0])
        for r in range(height):
            if index:
                out[r].append(0)
            out[r].extend(tile[r] if r < len(tile) else [0] * width)
    return out
