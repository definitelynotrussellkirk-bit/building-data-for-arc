"""Visible-example solution for the blind ARC task."""


def _segments(length, separators):
    """Return half-open non-separator intervals."""
    result = []
    start = 0
    for stop in [*separators, length]:
        if start < stop:
            result.append((start, stop))
        start = stop + 1
    return result


def solve(grid):
    """Collapse a tiled grid, marking any inconsistent tile cell with color 1."""
    height = len(grid)
    width = len(grid[0])

    separator_rows = [r for r, row in enumerate(grid) if len(set(row)) == 1]
    separator_cols = [
        c for c in range(width) if len({grid[r][c] for r in range(height)}) == 1
    ]

    row_blocks = _segments(height, separator_rows)
    col_blocks = _segments(width, separator_cols)
    tiles = [
        [row[c0:c1] for row in grid[r0:r1]]
        for r0, r1 in row_blocks
        for c0, c1 in col_blocks
    ]

    tile_height = len(tiles[0])
    tile_width = len(tiles[0][0])
    return [
        [
            1
            if len({tile[r][c] for tile in tiles}) > 1
            else tiles[0][r][c]
            for c in range(tile_width)
        ]
        for r in range(tile_height)
    ]
