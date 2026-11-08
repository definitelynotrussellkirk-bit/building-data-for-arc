"""Restore a rectangular periodic tiling whose missing cells are colored 0."""


def _infer_tile(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0

    candidates = []
    for row_period in range(1, height + 1):
        for col_period in range(1, width + 1):
            tile = {}
            valid = True
            for row_index, row in enumerate(grid):
                if len(row) != width:
                    raise ValueError("grid must be rectangular")
                for col_index, color in enumerate(row):
                    if color == 0:
                        continue
                    key = (row_index % row_period, col_index % col_period)
                    previous = tile.get(key)
                    if previous is not None and previous != color:
                        valid = False
                        break
                    tile[key] = color
                if not valid:
                    break

            # A usable period must determine every position of its base tile.
            if valid and len(tile) == row_period * col_period:
                candidates.append(
                    (row_period * col_period, row_period + col_period,
                     row_period, col_period, tile)
                )

    if not candidates:
        raise ValueError("could not infer a fully observed periodic tile")

    _, _, row_period, col_period, tile = min(candidates)
    return row_period, col_period, tile


def solve(grid):
    if not grid:
        return []

    row_period, col_period, tile = _infer_tile(grid)
    return [
        [tile[(row_index % row_period, col_index % col_period)]
         for col_index in range(len(row))]
        for row_index, row in enumerate(grid)
    ]
