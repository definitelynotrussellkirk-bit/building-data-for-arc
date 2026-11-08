def solve(grid):
    """Restore zero cells from the smallest consistent repeating tile."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    periods = sorted(
        ((ph, pw) for ph in range(1, height + 1)
         for pw in range(1, width + 1)),
        key=lambda period: (period[0] * period[1], period[0], period[1]),
    )
    for ph, pw in periods:
        tile = {}
        consistent = True
        for r, row in enumerate(grid):
            for c, color in enumerate(row):
                if color == 0:
                    continue
                key = (r % ph, c % pw)
                if key in tile and tile[key] != color:
                    consistent = False
                    break
                tile[key] = color
            if not consistent:
                break
        if consistent and len(tile) == ph * pw:
            return [
                [tile[r % ph, c % pw] if color == 0 else color
                 for c, color in enumerate(row)]
                for r, row in enumerate(grid)
            ]
    # Do not guess a color when the surviving cells cannot determine a tile.
    return [list(row) for row in grid]
