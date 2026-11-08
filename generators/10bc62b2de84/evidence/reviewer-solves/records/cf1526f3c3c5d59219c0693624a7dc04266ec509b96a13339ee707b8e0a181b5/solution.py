from __future__ import annotations


def solve(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    objects = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    stack.append(point)
        objects.append(cells)

    objects.sort(key=lambda cells: min(c for _, c in cells))
    pieces = []
    for cells in objects:
        r1 = min(r for r, _ in cells)
        r2 = max(r for r, _ in cells)
        c1 = min(c for _, c in cells)
        c2 = max(c for _, c in cells)
        pieces.append([row[c1:c2 + 1] for row in grid[r1:r2 + 1]])

    out_h = max(len(piece) for piece in pieces)
    out_w = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    out = [[0] * out_w for _ in range(out_h)]
    left = 0
    for piece in pieces:
        top = out_h - len(piece)
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                if value != 0:
                    out[top + r][left + c] = value
        left += len(piece[0]) + 1
    return out
