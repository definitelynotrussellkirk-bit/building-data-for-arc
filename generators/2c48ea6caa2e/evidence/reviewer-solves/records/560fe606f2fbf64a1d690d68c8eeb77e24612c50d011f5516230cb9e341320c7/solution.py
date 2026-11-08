def solve(grid):
    """Complete the broken rectangle and supported internal straight dividers."""
    result = [row[:] for row in grid]
    points = [(r, c) for r, row in enumerate(grid)
              for c, value in enumerate(row) if value == 1]
    if not points:
        return result
    top = min(r for r, c in points)
    bottom = max(r for r, c in points)
    left = min(c for r, c in points)
    right = max(c for r, c in points)

    horizontal = {top, bottom}
    vertical = {left, right}
    # Interior evidence distinguishes a divider from isolated perimeter pixels.
    for r in range(top + 1, bottom):
        if sum(grid[r][c] == 1 for c in range(left + 1, right)) >= 2:
            horizontal.add(r)
    for c in range(left + 1, right):
        if sum(grid[r][c] == 1 for r in range(top + 1, bottom)) >= 2:
            vertical.add(c)

    for r in horizontal:
        for c in range(left, right + 1):
            if result[r][c] == 0:
                result[r][c] = 2
    for c in vertical:
        for r in range(top, bottom + 1):
            if result[r][c] == 0:
                result[r][c] = 2
    return result
