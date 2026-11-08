"""Post-repair visible-example solve with prior exposure declared in notes."""


def solve(grid):
    h, w = len(grid), len(grid[0])
    cyan = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if not cyan:
        return [list(row) for row in grid]
    top = min(r for r, c in cyan)
    bottom = max(r for r, c in cyan)
    left = min(c for r, c in cyan)
    right = max(c for r, c in cyan)
    out = [list(row) for row in grid]
    rays = []
    for r in range(top, bottom + 1):
        rays.extend(((r, left - 1, 0, -1), (r, right + 1, 0, 1)))
    for c in range(left, right + 1):
        rays.extend(((top - 1, c, -1, 0), (bottom + 1, c, 1, 0)))
    for r, c, dr, dc in rays:
        while 0 <= r < h and 0 <= c < w:
            if grid[r][c] not in (0, 2):
                break
            out[r][c] = 4
            r += dr
            c += dc
    return out
