def solve(grid):
    """Crop the first two nonzero objects and overlay them at top-left."""
    h, w = len(grid), len(grid[0])
    seen = set()
    objects = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            objects.append((color, cells))

    normalized = []
    for color, cells in objects[:2]:
        r0 = min(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        normalized.append((color, {(r - r0, c - c0) for r, c in cells}))

    (first_color, first), (second_color, second) = normalized
    out_h = max(max(r for r, _ in first), max(r for r, _ in second)) + 1
    out_w = max(max(c for _, c in first), max(c for _, c in second)) + 1
    return [
        [8 if (r, c) in first and (r, c) in second
         else first_color if (r, c) in first
         else second_color if (r, c) in second
         else 0
         for c in range(out_w)]
        for r in range(out_h)
    ]
