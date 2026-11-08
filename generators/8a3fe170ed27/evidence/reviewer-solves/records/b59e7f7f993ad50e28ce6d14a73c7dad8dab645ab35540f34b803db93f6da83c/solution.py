from collections import Counter


def solve(grid):
    """Apply the visible row-wise four-step horizontal wave."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]

    occupied_rows = [
        r for r, row in enumerate(grid) if any(value != background for value in row)
    ]
    if not occupied_rows:
        return [row[:] for row in grid]

    top = occupied_rows[0]
    foreground_columns = [
        c
        for row in grid
        for c, value in enumerate(row)
        if value != background
    ]
    left = min(foreground_columns)

    # The visible phase cue is the extra upper-left cell on the second
    # occupied row.  With the cue, the first wave step goes left; without
    # it, the first wave step goes right.
    second_row = occupied_rows[1] if len(occupied_rows) > 1 else top
    has_left_phase_cue = (
        left + 1 < width and grid[second_row][left + 1] != background
    )
    phase = -1 if has_left_phase_cue else 1
    offsets = (phase, 0, -phase, 0)

    result = [[background for _ in range(width)] for _ in range(height)]
    for r, row in enumerate(grid):
        offset = offsets[(r - top) % 4]
        for c, value in enumerate(row):
            if value == background:
                continue
            shifted = c + offset
            if 0 <= shifted < width:
                result[r][shifted] = value
    return result
