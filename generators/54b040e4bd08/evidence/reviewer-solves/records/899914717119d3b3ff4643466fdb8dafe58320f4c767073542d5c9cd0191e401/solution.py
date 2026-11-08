def solve(grid):
    """Restore zeroed cells in the smallest consistent rectangular tiling."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    if not height or not width:
        return [row[:] for row in grid]

    candidates = []
    for row_period in range(1, height + 1):
        for col_period in range(1, width + 1):
            tile = {}
            consistent = True
            for r, row in enumerate(grid):
                for c, value in enumerate(row):
                    if value == 0:
                        continue
                    key = (r % row_period, c % col_period)
                    previous = tile.get(key)
                    if previous is not None and previous != value:
                        consistent = False
                        break
                    tile[key] = value
                if not consistent:
                    break
            if not consistent:
                continue
            if any(
                value == 0 and (r % row_period, c % col_period) not in tile
                for r, row in enumerate(grid)
                for c, value in enumerate(row)
            ):
                continue
            candidates.append((row_period * col_period, row_period + col_period,
                               row_period, col_period, tile))

    if not candidates:
        return [row[:] for row in grid]

    _, _, row_period, col_period, tile = min(candidates)
    return [
        [tile[(r % row_period, c % col_period)] if value == 0 else value
         for c, value in enumerate(row)]
        for r, row in enumerate(grid)
    ]
