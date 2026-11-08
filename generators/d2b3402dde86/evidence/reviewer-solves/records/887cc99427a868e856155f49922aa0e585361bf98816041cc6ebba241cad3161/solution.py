def solve(grid):
    nonzero = [(r, c) for r, row in enumerate(grid)
               for c, color in enumerate(row) if color != 0]
    if not nonzero:
        raise ValueError("No foreground bounding box")
    top = min(r for r, c in nonzero)
    left = min(c for r, c in nonzero)
    bottom = max(r for r, c in nonzero)
    right = max(c for r, c in nonzero)
    height = (bottom - top + 1) // 2
    width = (right - left + 1) // 2
    return [list(row[left:left + width]) for row in grid[top:top + height]]
