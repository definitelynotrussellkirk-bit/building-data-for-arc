def solve(grid):
    """Apply the color substitutions encoded above the first blank row.

    The first two rows form vertical (source, destination) color pairs.  The
    all-zero row separates this legend from the picture.  Return only the
    picture, replacing each legend source color by its paired destination and
    leaving all other colors unchanged.
    """
    separator = next(i for i, row in enumerate(grid) if all(cell == 0 for cell in row))
    legend = grid[:separator]
    if len(legend) < 2:
        raise ValueError("expected a two-row substitution legend")

    mapping = {
        source: destination
        for source, destination in zip(legend[0], legend[1])
        if source != 0 and destination != 0
    }
    return [
        [mapping.get(cell, cell) for cell in row]
        for row in grid[separator + 1 :]
    ]
