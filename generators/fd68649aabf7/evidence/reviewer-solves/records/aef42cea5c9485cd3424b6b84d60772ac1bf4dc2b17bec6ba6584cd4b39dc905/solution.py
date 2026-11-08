def solve(grid):
    """Recolor each four-connected body using its nearest header marker."""
    out = [list(row) for row in grid]
    if not grid:
        return out
    markers = [(c, value) for c, value in enumerate(grid[0]) if value != 0]
    if not markers:
        return out
    height, width = len(grid), len(grid[0])
    seen = set()
    for r in range(1, height):
        for c in range(width):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            cells = [(r, c)]
            seen.add((r, c))
            for rr, cc in cells:
                for nr, nc in ((rr-1, cc), (rr+1, cc), (rr, cc-1), (rr, cc+1)):
                    if (1 <= nr < height and 0 <= nc < width
                            and grid[nr][nc] != 0 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        cells.append((nr, nc))
            left = min(cc for _, cc in cells)
            _, color = min(markers, key=lambda marker: (abs(marker[0]-left), -marker[0]))
            for rr, cc in cells:
                out[rr][cc] = color
    return out
