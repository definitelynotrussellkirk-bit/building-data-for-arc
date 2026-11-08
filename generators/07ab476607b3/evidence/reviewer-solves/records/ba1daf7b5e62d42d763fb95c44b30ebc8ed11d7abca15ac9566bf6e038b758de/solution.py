def solve(grid):
    """Stamp the red-only part of the normalized red/yellow overlay at color 9."""
    height = len(grid)
    width = len(grid[0]) if height else 0

    red = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    yellow = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 4]
    marker = next(
        ((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9),
        None,
    )

    output = [[0 for _ in range(width)] for _ in range(height)]
    if not red or not yellow or marker is None:
        return output

    red_top = min(r for r, _ in red)
    red_left = min(c for _, c in red)
    yellow_top = min(r for r, _ in yellow)
    yellow_left = min(c for _, c in yellow)

    red_shape = {(r - red_top, c - red_left) for r, c in red}
    yellow_shape = {(r - yellow_top, c - yellow_left) for r, c in yellow}

    marker_r, marker_c = marker
    for dr, dc in red_shape - yellow_shape:
        r = marker_r + dr
        c = marker_c + dc
        if 0 <= r < height and 0 <= c < width:
            output[r][c] = 6

    return output
