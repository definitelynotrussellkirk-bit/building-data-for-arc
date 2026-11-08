from copy import deepcopy


def solve(grid):
    """Pour yellow through the one open side of the colored frame."""
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    color = next(v for row in grid for v in row if v not in (0, 4))
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)

    sides = {
        "top": [grid[r0][c] == color for c in range(c0, c1 + 1)],
        "bottom": [grid[r1][c] == color for c in range(c0, c1 + 1)],
        "left": [grid[r][c0] == color for r in range(r0, r1 + 1)],
        "right": [grid[r][c1] == color for r in range(r0, r1 + 1)],
    }
    side = next(name for name, occupied in sides.items() if not all(occupied))
    occupied = sides[side]
    missing = [i for i, present in enumerate(occupied) if not present]
    before = missing[0]
    after = len(occupied) - missing[-1] - 1

    def paint(r, c):
        if 0 <= r < h and 0 <= c < w and out[r][c] == 0:
            out[r][c] = 4

    if side in ("left", "right"):
        top_tip = r0 + before - 1
        bottom_tip = r1 - after + 1
        mouth_c = c0 - 1 if side == "left" else c1 + 1
        for r in range(top_tip + 1, bottom_tip):
            cols = range(0, c1 + 1) if side == "left" else range(c0, w)
            for c in cols:
                paint(r, c)
        for r in (top_tip, bottom_tip):
            paint(r, mouth_c)
            cols = range(c0 + 1, c1 + 1) if side == "left" else range(c0, c1)
            for c in cols:
                paint(r, c)
        direction = -1 if side == "left" else 1
        for d in range(1, max(h, w) + 1):
            paint(top_tip - d, mouth_c + direction * d)
            paint(bottom_tip + d, mouth_c + direction * d)
    else:
        left_tip = c0 + before - 1
        right_tip = c1 - after + 1
        mouth_r = r0 - 1 if side == "top" else r1 + 1
        for c in range(left_tip + 1, right_tip):
            rows = range(0, r1 + 1) if side == "top" else range(r0, h)
            for r in rows:
                paint(r, c)
        for c in (left_tip, right_tip):
            paint(mouth_r, c)
            rows = range(r0 + 1, r1 + 1) if side == "top" else range(r0, r1)
            for r in rows:
                paint(r, c)
        direction = -1 if side == "top" else 1
        for d in range(1, max(h, w) + 1):
            paint(mouth_r + direction * d, left_tip - d)
            paint(mouth_r + direction * d, right_tip + d)
    return out
