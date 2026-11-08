"""Solve the visible tile-and-swatch transformation from the supplied grid."""

def _runs(flags):
    """Half-open spans where a separator flag is false."""
    spans = []
    beginning = None
    for index, separated in enumerate(flags + [True]):
        if not separated and beginning is None:
            beginning = index
        elif separated and beginning is not None:
            spans.append((beginning, index))
            beginning = None
    return spans


def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('Expected a nonempty rectangular input')
    height, width = len(grid), len(grid[0])
    horizontal = _runs([all(value == 8 for value in row) for row in grid])
    vertical = _runs([all(grid[row][col] == 8 for row in range(height))
                      for col in range(width)])
    if not horizontal or not vertical:
        raise ValueError('Missing visible tile lattice')
    side = horizontal[0][1] - horizontal[0][0]
    if side < 3 or any(bottom - top != side for top, bottom in horizontal):
        raise ValueError('The tile rows must have one common height')
    swatch_col = vertical[0][0]
    swatches = []
    for top, bottom in horizontal:
        values = {grid[row][swatch_col] for row in range(top, bottom)}
        if len(values) != 1:
            raise ValueError('A row swatch must be uniform')
        swatches.append(next(iter(values)))
    output_tiles = []
    for column, (left, right) in enumerate(vertical):
        start = left + (1 if column == 0 else 0)
        if right - start != side:
            raise ValueError('The visible tiles must be square')
        tiles = [[list(row[start:right]) for row in grid[top:bottom]]
                 for top, bottom in horizontal]
        solid = []
        for row, tile in enumerate(tiles):
            inside = {value for line in tile[1:-1] for value in line[1:-1]}
            if len(inside) == 1:
                fill = next(iter(inside))
                if fill not in (1, 2, 8):
                    solid.append((row, fill))
        if len(solid) != 1:
            raise ValueError('Each tile column needs one solid-color cue')
        cue_row, fill = solid[0]
        patterns = [tile for row, tile in enumerate(tiles) if row != cue_row]
        if not patterns or any(tile != patterns[0] for tile in patterns[1:]):
            raise ValueError('The other tiles must duplicate one pattern')
        frame = swatches[cue_row]
        output_tiles.append([[frame if value == 1 else fill if value == 2 else value
                              for value in row] for row in patterns[0]])
    output = []
    for row in range(side):
        line = []
        for column, tile in enumerate(output_tiles):
            if column:
                line.append(8)
            line.extend(tile[row])
        output.append(line)
    return output
