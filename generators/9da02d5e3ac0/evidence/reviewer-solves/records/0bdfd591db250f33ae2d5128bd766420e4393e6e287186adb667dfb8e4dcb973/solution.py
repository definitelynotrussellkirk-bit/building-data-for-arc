def solve(grid):
    """Recolor each gray payload row using that row's embedded color key."""
    output = [row[:] for row in grid]

    for row_index, row in enumerate(grid):
        # The all-gray final row is a literal footer/boundary, not payload.
        if row and all(value == 5 for value in row):
            continue

        keys = {value for value in row if value not in (0, 5)}
        if len(keys) != 1:
            # No unambiguous row key: leave the row unchanged rather than guess.
            continue

        key = next(iter(keys))
        # The first row encodes its key as [0, key, ...]; its gray cells erase
        # to background instead of being painted.
        replacement = 0 if len(row) >= 2 and row[0] == 0 and row[1] == key else key
        output[row_index] = [replacement if value == 5 else value for value in row]

    return output
