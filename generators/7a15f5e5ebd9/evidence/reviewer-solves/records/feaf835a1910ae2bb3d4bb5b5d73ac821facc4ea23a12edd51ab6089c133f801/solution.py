def solve(grid):
    """Stamp the yellow template around every red marker.

    The maroon cell is the template's anchor.  Its position is replaced by each
    red cell; yellow cells retain their offsets from the anchor.  The source
    template disappears, stamps are clipped at the grid boundary, and red
    markers take precedence when a stamp overlaps one.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0

    anchor = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    )
    anchor_r, anchor_c = anchor

    yellow_offsets = [
        (r - anchor_r, c - anchor_c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 4
    ]
    red_markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    red_set = set(red_markers)

    output = [[0 for _ in range(width)] for _ in range(height)]
    for marker_r, marker_c in red_markers:
        output[marker_r][marker_c] = 2

    for marker_r, marker_c in red_markers:
        for dr, dc in yellow_offsets:
            r = marker_r + dr
            c = marker_c + dc
            if 0 <= r < height and 0 <= c < width and (r, c) not in red_set:
                output[r][c] = 4

    return output
