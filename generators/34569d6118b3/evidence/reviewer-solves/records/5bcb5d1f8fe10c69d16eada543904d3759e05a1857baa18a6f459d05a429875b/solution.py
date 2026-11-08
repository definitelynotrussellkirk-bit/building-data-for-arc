from __future__ import annotations


def _runs(values, predicate):
    """Return half-open index runs whose values satisfy predicate."""
    runs = []
    start = None
    for i, value in enumerate(values):
        if predicate(value):
            if start is None:
                start = i
        elif start is not None:
            runs.append((start, i))
            start = None
    if start is not None:
        runs.append((start, len(values)))
    return runs


def solve(grid):
    """Expand the lower symbol grid with the keyed binary stamps above it."""
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])

    # The first completely blank row separates the stamp legend from the
    # lower symbol grid.  Consecutive blank rows are all part of the separator.
    split = next(
        (r for r in range(1, height) if all(value == 0 for value in grid[r])),
        None,
    )
    if split is None:
        raise ValueError("no blank separator row")

    # The marker used for every binary stamp is the nonzero value that occurs
    # most often in the upper region.  In the supplied examples it is 5.
    upper_values = [
        value
        for row in grid[:split]
        for value in row
        if value != 0
    ]
    if not upper_values:
        raise ValueError("empty stamp legend")
    counts = {value: upper_values.count(value) for value in set(upper_values)}
    marker = max(counts, key=lambda value: (counts[value], value))

    stamp_runs = _runs(grid[0], lambda value: value == marker)
    if not stamp_runs:
        raise ValueError("no stamp blocks on top row")

    first_stamp_col = stamp_runs[0][0]
    key_runs = _runs(
        grid[0][:first_stamp_col],
        lambda value: value != 0 and value != marker,
    )
    keys = [grid[0][start] for start, _ in key_runs]
    if len(keys) != len(stamp_runs):
        raise ValueError("key/stamp count mismatch")

    stamps = {}
    for key, (left, right) in zip(keys, stamp_runs):
        stamps[key] = [
            [1 if value == marker else 0 for value in row[left:right]]
            for row in grid[:split]
        ]

    # Skip all separator rows, then crop the lower symbol grid to its nonzero
    # bounding box.  Zeros inside that box are meaningful background symbols.
    lower_start = split
    while lower_start < height and all(value == 0 for value in grid[lower_start]):
        lower_start += 1
    lower_cells = [
        (r, c)
        for r in range(lower_start, height)
        for c in range(width)
        if grid[r][c] != 0
    ]
    if not lower_cells:
        return []
    top = min(r for r, _ in lower_cells)
    bottom = max(r for r, _ in lower_cells) + 1
    left = min(c for _, c in lower_cells)
    right = max(c for _, c in lower_cells) + 1
    symbols = [row[left:right] for row in grid[top:bottom]]

    stamp_h = split
    stamp_w = stamp_runs[0][1] - stamp_runs[0][0]
    if any((end - start) != stamp_w for start, end in stamp_runs):
        raise ValueError("inconsistent stamp widths")

    output = []
    for symbol_row in symbols:
        expanded_rows = [[] for _ in range(stamp_h)]
        for symbol in symbol_row:
            if symbol == 0:
                stamp = [[0] * stamp_w for _ in range(stamp_h)]
            else:
                stamp = stamps[symbol]
            for r in range(stamp_h):
                expanded_rows[r].extend(
                    symbol if bit else 0 for bit in stamp[r]
                )
        output.extend(expanded_rows)
    return output
