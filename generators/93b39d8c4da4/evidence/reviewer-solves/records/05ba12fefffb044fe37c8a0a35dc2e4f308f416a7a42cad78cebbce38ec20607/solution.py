def solve(grid):
    """Stamp the red template at each green top-left anchor, using azure."""
    height, width = len(grid), len(grid[0])
    template = [(r, c) for r, row in enumerate(grid)
                for c, value in enumerate(row) if value == 2]
    anchors = [(r, c) for r, row in enumerate(grid)
               for c, value in enumerate(row) if value == 3]
    out = [[0] * width for _ in range(height)]
    if not template:
        return out
    top = min(r for r, _ in template)
    left = min(c for _, c in template)
    offsets = [(r - top, c - left) for r, c in template]
    for ar, ac in anchors:
        for dr, dc in offsets:
            r, c = ar + dr, ac + dc
            if 0 <= r < height and 0 <= c < width:
                out[r][c] = 8
    return out
