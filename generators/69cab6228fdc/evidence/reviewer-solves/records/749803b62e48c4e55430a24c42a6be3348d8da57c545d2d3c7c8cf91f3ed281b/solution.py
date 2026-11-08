def solve(grid):
    """Decode vertical color-pair legend above the blank separator row."""
    if not grid:
        return []

    separator = next(
        (r for r, row in enumerate(grid) if all(value == 0 for value in row)),
        None,
    )
    if separator is None or separator < 2:
        raise ValueError("expected a two-row legend followed by a blank separator")

    source_row = grid[separator - 2]
    target_row = grid[separator - 1]
    mapping = {
        source: target
        for source, target in zip(source_row, target_row)
        if source != 0
    }

    return [
        [mapping.get(value, value) for value in row]
        for row in grid[separator + 1 :]
    ]
