def solve(grid):
    """Rotate each monochrome 4-connected object clockwise in its tight box."""
    h, w = len(grid), len(grid[0])
    seen = set()
    objects = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            objects.append((color, cells))

    out = [[0] * w for _ in range(h)]
    for color, cells in objects:
        r0 = min(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        r1 = max(r for r, _ in cells)
        box_h = r1 - r0 + 1
        rotated = [(c-c0, box_h-1-(r-r0)) for r, c in cells]
        min_r = min(r for r, _ in rotated)
        min_c = min(c for _, c in rotated)
        for rr, cc in rotated:
            out[r0 + rr - min_r][c0 + cc - min_c] = color
    return out
