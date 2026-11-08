def solve(grid):
    """Extend each nonzero, non-5 cell rightward until a 5 or row edge."""
    out = [row[:] for row in grid]
    for row in out:
        width = len(row)
        for col, value in enumerate(row):
            if value in (0, 5):
                continue
            stop = col + 1
            while stop < width and row[stop] != 5:
                # Canonical examples have one source per segment.  Preserve any
                # pre-existing nonzero marker rather than painting over it.
                if row[stop] != 0:
                    break
                row[stop] = value
                stop += 1
    return out
