"""Blind solution inferred from visible examples only."""


def solve(grid):
    """Fill each region split by the color-5 cross from local marker counts.

    In each of the four rectangular regions, preserve colors 2/3/4 and replace
    zeros by 6/7/8 when 2/3/4 is the unique most frequent marker.  Use 9 when
    the maximum count is tied.  Preserve every color-5 divider cell.
    """
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    divider_rows = [r for r, row in enumerate(grid) if row and all(v == 5 for v in row)]
    divider_cols = [
        c for c in range(width)
        if height and all(grid[r][c] == 5 for r in range(height))
    ]
    if len(divider_rows) != 1 or len(divider_cols) != 1:
        raise ValueError("expected exactly one full color-5 divider row and column")

    split_r = divider_rows[0]
    split_c = divider_cols[0]
    regions = (
        (range(0, split_r), range(0, split_c)),
        (range(0, split_r), range(split_c + 1, width)),
        (range(split_r + 1, height), range(0, split_c)),
        (range(split_r + 1, height), range(split_c + 1, width)),
    )
    fill_for_marker = {2: 6, 3: 7, 4: 8}

    for rows, cols in regions:
        rows = tuple(rows)
        cols = tuple(cols)
        counts = {marker: 0 for marker in fill_for_marker}
        for r in rows:
            for c in cols:
                value = grid[r][c]
                if value in counts:
                    counts[value] += 1

        best = max(counts.values())
        winners = [marker for marker, count in counts.items() if count == best]
        fill = fill_for_marker[winners[0]] if len(winners) == 1 else 9

        for r in rows:
            for c in cols:
                if grid[r][c] == 0:
                    out[r][c] = fill

    return out
