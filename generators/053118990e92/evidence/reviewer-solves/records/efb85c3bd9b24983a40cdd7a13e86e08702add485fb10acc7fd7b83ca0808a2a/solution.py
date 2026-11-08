def solve(grid):
    """Fill the 8-delimited interior by Manhattan-nearest seed color.

    Cells tied between different nearest colors remain background.  The 8-valued
    frame/corners, original seeds, and every cell outside the frame are preserved.
    """
    out = [row[:] for row in grid]
    eight_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    if not eight_cells:
        return out

    top = min(r for r, _ in eight_cells)
    bottom = max(r for r, _ in eight_cells)
    left = min(c for _, c in eight_cells)
    right = max(c for _, c in eight_cells)

    seeds = [
        (r, c, grid[r][c])
        for r in range(top + 1, bottom)
        for c in range(left + 1, right)
        if grid[r][c] not in (0, 8)
    ]

    for r in range(top + 1, bottom):
        for c in range(left + 1, right):
            if grid[r][c] != 0:
                continue
            best_distance = None
            nearest_colors = set()
            for seed_r, seed_c, color in seeds:
                distance = abs(r - seed_r) + abs(c - seed_c)
                if best_distance is None or distance < best_distance:
                    best_distance = distance
                    nearest_colors = {color}
                elif distance == best_distance:
                    nearest_colors.add(color)
            if len(nearest_colors) == 1:
                out[r][c] = nearest_colors.pop()

    return out
