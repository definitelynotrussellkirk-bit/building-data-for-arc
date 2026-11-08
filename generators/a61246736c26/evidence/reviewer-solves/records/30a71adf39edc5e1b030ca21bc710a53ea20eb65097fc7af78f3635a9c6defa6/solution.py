"""Visible-example solution for blind task a61246736c26."""


def _all_equal(values, value):
    return all(cell == value for row in values for cell in row)


def _split_bands(grid):
    height = len(grid)
    width = len(grid[0])

    divider_rows = [
        r for r in range(height)
        if all(grid[r][c] == 8 for c in range(width))
    ]
    divider_cols = [
        c for c in range(width)
        if all(grid[r][c] == 8 for r in range(height))
    ]

    bands = []
    for top, bottom in zip(divider_rows, divider_rows[1:]):
        region = [row[:] for row in grid[top + 1:bottom]]
        label = region[0][0]

        tiles = []
        # The first region carries one extra leading column containing the
        # row's label color. Removing it makes all tiles the same size.
        tiles.append([row[1:divider_cols[0]] for row in region])
        for left, right in zip(divider_cols, divider_cols[1:]):
            tiles.append([row[left + 1:right] for row in region])
        bands.append((label, tiles))

    return bands


def _interior(tile):
    return [row[1:-1] for row in tile[1:-1]]


def solve(grid):
    """Fuse each repeated shape with the solid swatch in the same column."""
    bands = _split_bands(grid)
    tile_count = len(bands[0][1])
    rendered = []

    for tile_index in range(tile_count):
        entries = [(label, tiles[tile_index]) for label, tiles in bands]

        solid_entries = []
        for label, tile in entries:
            inside = _interior(tile)
            values = {cell for row in inside for cell in row}
            if len(values) == 1:
                fill = next(iter(values))
                if fill not in {1, 2, 8}:
                    solid_entries.append((label, fill))

        if len(solid_entries) != 1:
            raise ValueError("expected one solid color swatch per tile column")
        label, fill = solid_entries[0]

        pattern_tiles = []
        for _, tile in entries:
            values = {cell for row in _interior(tile) for cell in row}
            if values <= {2, 8} and 2 in values:
                pattern_tiles.append(tile)
        if not pattern_tiles:
            raise ValueError("expected a 2/8 shape template per tile column")
        pattern = pattern_tiles[0]

        rendered_tile = []
        for row in pattern:
            rendered_tile.append([
                label if cell == 1 else fill if cell == 2 else cell
                for cell in row
            ])
        rendered.append(rendered_tile)

    output = [[] for _ in range(len(rendered[0]))]
    for index, tile in enumerate(rendered):
        if index:
            for row in output:
                row.append(8)
        for r, row in enumerate(tile):
            output[r].extend(row)
    return output
