def solve(grid):
    out = [list(row) for row in grid]
    frames = []
    for color in {v for row in grid for v in row} - {0}:
        cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
        top, bottom = min(r for r,c in cells), max(r for r,c in cells)
        left, right = min(c for r,c in cells), max(c for r,c in cells)
        if bottom-top >= 2 and right-left >= 2 and all(grid[r][c] == color for r in range(top,bottom+1) for c in range(left,right+1) if r in (top,bottom) or c in (left,right)):
            frames.append(((bottom-top)*(right-left), top, bottom, left, right))
    if not frames:
        raise ValueError("No solid rectangular frame")
    _, top, bottom, left, right = max(frames)
    for c in range(left+1, right):
        values = [grid[r][c] for r in range(top+1,bottom) if grid[r][c] != 0]
        for k, r in enumerate(range(top+1,bottom)):
            out[r][c] = values[k] if k < len(values) else 0
    return out
