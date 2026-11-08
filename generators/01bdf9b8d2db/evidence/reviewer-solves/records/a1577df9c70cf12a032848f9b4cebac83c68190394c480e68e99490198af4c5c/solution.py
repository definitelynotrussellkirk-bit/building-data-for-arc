def solve(grid):
    """Fill each 4-connected non-5 chamber with its unique nonzero seed."""
    h, w = len(grid), len(grid[0])
    out = [[5 if value == 5 else 0 for value in row] for row in grid]
    seen = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 5 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            region = []
            while stack:
                cr, cc = stack.pop()
                region.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            grid[nr][nc] != 5 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            seeds = [grid[rr][cc] for rr, cc in region if grid[rr][cc] not in (0, 5)]
            if not seeds:
                color = 0
            else:
                color = seeds[0]
            for rr, cc in region:
                out[rr][cc] = color
    return out
