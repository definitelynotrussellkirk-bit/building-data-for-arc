def solve(grid):
    """Collapse each input column of three framed tiles into one answer tile.

    In every tile-column, two row-bands contain the same sparse 4x4 mask and
    the remaining row-band contains a solid 4x4 color swatch.  The output tile
    uses the swatch row's left-hand label as its frame and paints the repeated
    sparse mask with the swatch color.  Tile-columns stay in left-to-right
    order and retain the separator color between them.
    """
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    separator = grid[0][0]

    # The visible layout consists of six-row bands separated by full rows of
    # the separator color.  Detect the band starts rather than hard-coding
    # their count.
    band_starts = []
    in_band = False
    for row_index, row in enumerate(grid):
        is_separator_row = all(value == separator for value in row)
        if not is_separator_row and not in_band:
            band_starts.append(row_index)
            in_band = True
        elif is_separator_row:
            in_band = False

    # Each tile is six columns wide, preceded by the left label column for the
    # first tile and followed by a one-column separator: starts 1, 8, 15, ...
    tile_starts = list(range(1, width - 1, 7))
    output_tiles = []

    for tile_start in tile_starts:
        candidates = []
        for band_start in band_starts:
            interior = tuple(
                tuple(grid[row][tile_start + 1 : tile_start + 5])
                for row in range(band_start + 1, band_start + 5)
            )
            label = grid[band_start][0]
            candidates.append((label, interior))

        solid_candidates = [
            (label, interior)
            for label, interior in candidates
            if len({value for row in interior for value in row}) == 1
            and interior[0][0] != separator
        ]
        if len(solid_candidates) != 1:
            raise ValueError(
                f"expected one solid swatch in tile column {tile_start}, "
                f"found {len(solid_candidates)}"
            )

        frame_color, solid = solid_candidates[0]
        paint_color = solid[0][0]
        masks = [
            interior
            for label, interior in candidates
            if (label, interior) != (frame_color, solid)
        ]
        if not masks or any(mask != masks[0] for mask in masks[1:]):
            raise ValueError(
                f"expected matching sparse masks in tile column {tile_start}"
            )
        mask = masks[0]

        tile = [[frame_color for _ in range(6)] for _ in range(6)]
        for row in range(4):
            for column in range(4):
                tile[row + 1][column + 1] = (
                    separator if mask[row][column] == separator else paint_color
                )
        output_tiles.append(tile)

    result = [[] for _ in range(6)]
    for index, tile in enumerate(output_tiles):
        if index:
            for row in result:
                row.append(separator)
        for row_index in range(6):
            result[row_index].extend(tile[row_index])
    return result
