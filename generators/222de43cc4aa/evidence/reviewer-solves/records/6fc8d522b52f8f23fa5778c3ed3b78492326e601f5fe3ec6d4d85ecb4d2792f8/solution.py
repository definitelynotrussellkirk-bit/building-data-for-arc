def solve(grid):
    """Repeat the row pattern through two vertical mirror cycles."""
    if not grid:
        return []
    if len(grid) == 1:
        return [list(grid[0])]

    # Walk top -> bottom -> top -> bottom -> top, without duplicating
    # either endpoint at a turn.  For five rows this is:
    # 0,1,2,3,4,3,2,1,0,1,2,3,4,3,2,1,0.
    h = len(grid)
    indices = (
        list(range(h))
        + list(range(h - 2, -1, -1))
        + list(range(1, h))
        + list(range(h - 2, -1, -1))
    )
    return [list(grid[i]) for i in indices]
