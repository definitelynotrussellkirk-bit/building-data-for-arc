def solve(grid):
    """Provisional spatial hypothesis inferred from the four visible pairs.

    Keep the uncertainty in SOLVE_NOTES.md: visible fit does not establish
    that this is the intended rule or that the masked predictions are right.
    """
    result = [list(row) for row in grid]
    if not grid or not grid[0]:
        return result
    h, w = len(grid), len(grid[0])
    visited = set()
    row_first = [next((c for c, value in enumerate(row) if value == 4), w)
                 for row in grid]
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 4 or (r, c) in visited:
                continue
            component = [(r, c)]
            visited.add((r, c))
            for rr, cc in component:
                for nr, nc in ((rr-1, cc), (rr+1, cc), (rr, cc-1), (rr, cc+1)):
                    if (0 <= nr < h and 0 <= nc < w and
                            grid[nr][nc] == 4 and (nr, nc) not in visited):
                        visited.add((nr, nc))
                        component.append((nr, nc))
            bottom = max(rr for rr, cc in component)
            left = min(cc for rr, cc in component if rr == bottom)
            if len(component) > 1 and left == row_first[bottom] and 2*left <= w-1:
                for rr, cc in component:
                    result[rr][cc] = 8
    return result
