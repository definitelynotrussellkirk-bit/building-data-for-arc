from __future__ import annotations


def _norm(panel):
    cells = [
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _transform(cells, t):
    out = []
    for r, c in cells:
        if t == 0:
            point = (r, c)
        elif t == 1:
            point = (c, -r)
        elif t == 2:
            point = (-r, -c)
        elif t == 3:
            point = (-c, r)
        elif t == 4:
            point = (r, -c)
        elif t == 5:
            point = (-c, -r)
        elif t == 6:
            point = (-r, c)
        else:
            point = (c, r)
        out.append(point)
    rr = min(r for r, _ in out)
    cc = min(c for _, c in out)
    return tuple(sorted((r - rr, c - cc) for r, c in out))


def solve(grid):
    n = (len(grid[0]) + 1) // 6
    panels = []
    for i in range(n):
        c0 = 6 * i
        panels.append(_norm([row[c0 : c0 + 5] for row in grid]))

    answer = [[0] * n for _ in range(n)]
    for i, a in enumerate(panels):
        rotations = {_transform(a, t) for t in range(4)}
        dihedral = {_transform(a, t) for t in range(8)}
        for j, b in enumerate(panels):
            if i == j:
                answer[i][j] = 8
            elif b == a:
                answer[i][j] = 1
            elif b in rotations:
                answer[i][j] = 2
            elif b in dihedral:
                answer[i][j] = 3
            else:
                answer[i][j] = 0
    return answer
