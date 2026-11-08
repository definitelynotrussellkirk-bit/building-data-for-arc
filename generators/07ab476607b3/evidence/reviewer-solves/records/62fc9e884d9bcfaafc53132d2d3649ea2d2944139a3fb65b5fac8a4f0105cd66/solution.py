def solve(grid):
    """Place the red-minus-yellow normalized shape at the maroon marker."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]

    red = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    yellow = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 4]
    markers = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    if not red or not markers:
        return output

    red_top = min(r for r, _ in red)
    red_left = min(c for _, c in red)
    yellow_normalized = set()
    if yellow:
        yellow_top = min(r for r, _ in yellow)
        yellow_left = min(c for _, c in yellow)
        yellow_normalized = {(r - yellow_top, c - yellow_left) for r, c in yellow}

    marker_r, marker_c = markers[0]
    for r, c in red:
        offset = (r - red_top, c - red_left)
        if offset in yellow_normalized:
            continue
        out_r = marker_r + offset[0]
        out_c = marker_c + offset[1]
        if 0 <= out_r < height and 0 <= out_c < width:
            output[out_r][out_c] = 6

    return output
