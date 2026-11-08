def solve(grid):
    """Find the shown foreground template and mark each occurrence's center."""
    h, w = len(grid), len(grid[0])
    separator = next(c for c in range(w)
                     if all(grid[r][c] == 9 for r in range(h)))
    template = [(r, c, grid[r][c]) for r in range(h)
                for c in range(separator) if grid[r][c] != 0]
    r0 = min(r for r, c, v in template)
    c0 = min(c for r, c, v in template)
    th = max(r for r, c, v in template) - r0 + 1
    tw = max(c for r, c, v in template) - c0 + 1
    pattern = [(r-r0, c-c0, v) for r, c, v in template]
    scene = [row[separator+1:] for row in grid]
    out = [[0] * len(scene[0]) for _ in scene]
    for r in range(h-th+1):
        for c in range(len(scene[0])-tw+1):
            if all(scene[r+dr][c+dc] == v for dr, dc, v in pattern):
                out[r+th//2][c+tw//2] = 8
    return out
