"""Visible-example solution for the generated ARC lesson."""


def solve(grid):
    """Stamp the bottom-left object's cardinal outline into bottom-right."""
    out = [row[:] for row in grid]
    if not grid or not grid[0]:
        return out

    height = len(grid)
    width = len(grid[0])

    separator_rows = [
        r for r, row in enumerate(grid)
        if len(row) == width and all(value == 9 for value in row)
    ]
    separator_cols = [
        c for c in range(width)
        if all(grid[r][c] == 9 for r in range(height))
    ]
    if not separator_rows or not separator_cols:
        return out

    split_r = separator_rows[0]
    split_c = separator_cols[0]

    source = []
    for r in range(split_r + 1, height):
        for c in range(split_c):
            value = grid[r][c]
            if value not in (0, 9):
                source.append((r - (split_r + 1), c, value))

    if not source:
        return out

    # The examples consistently use the first bottom-left nonzero cell's
    # color for the whole derived outline.
    stamp_color = source[0][2]
    occupied = {(r, c) for r, c, _ in source}

    # Cardinal boundary: a source cell is retained when at least one of its
    # four orthogonal neighbors is absent from the source union.
    outline = {
        (r, c)
        for r, c in occupied
        if any(
            (r + dr, c + dc) not in occupied
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        )
    }

    # Preserve the source's local offset within its quadrant, translate it
    # into the bottom-right quadrant, overwrite stamp positions, and clip.
    for local_r, local_c in outline:
        target_r = split_r + 1 + local_r
        target_c = split_c + 1 + local_c
        if 0 <= target_r < height and 0 <= target_c < width:
            out[target_r][target_c] = stamp_color

    return out
