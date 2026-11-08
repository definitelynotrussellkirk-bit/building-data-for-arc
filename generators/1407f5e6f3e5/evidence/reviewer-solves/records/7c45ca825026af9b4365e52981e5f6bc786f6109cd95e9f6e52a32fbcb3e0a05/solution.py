"""Visible-example solution: fill each same-color 4-connected component's bbox."""

STEPS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def solve(grid):
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    seen = set()
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            seen.add((r, c))
            todo = [(r, c)]
            cells = []
            for cr, cc in todo:
                cells.append((cr, cc))
                for dr, dc in STEPS:
                    point = cr + dr, cc + dc
                    if (0 <= point[0] < h and 0 <= point[1] < w
                            and point not in seen and grid[point[0]][point[1]] == color):
                        seen.add(point)
                        todo.append(point)
            r0 = min(x for x, _ in cells)
            r1 = max(x for x, _ in cells)
            c0 = min(y for _, y in cells)
            c1 = max(y for _, y in cells)
            for rr in range(r0, r1 + 1):
                for cc in range(c0, c1 + 1):
                    out[rr][cc] = color
    return out
