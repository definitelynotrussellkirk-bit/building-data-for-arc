def _cluster_nonzero(grid, radius):
    points = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    groups = []
    while points:
        seed = points.pop()
        group = {seed}
        stack = [seed]
        while stack:
            r, c = stack.pop()
            nearby = [
                point
                for point in points
                if max(abs(point[0] - r), abs(point[1] - c)) <= radius
            ]
            for point in nearby:
                points.remove(point)
                group.add(point)
                stack.append(point)
        groups.append(group)
    return groups


def solve(grid):
    """Pack four spatially arranged 3x3 glyphs into a 7x7 quadrant panel."""
    groups = _cluster_nonzero(grid, radius=1)
    if len(groups) != 4:
        # A glyph may contain separated dots inside one 3x3 tile. Radius two
        # still joins every pair of cells in such a tile while the four tiles
        # in the demonstrated layout remain spatially separated.
        groups = _cluster_nonzero(grid, radius=2)
    if len(groups) != 4:
        raise ValueError(f"expected four glyphs, found {len(groups)}")

    glyphs = []
    for group in groups:
        rows = [r for r, _ in group]
        cols = [c for _, c in group]
        r0, r1 = min(rows), max(rows)
        c0, c1 = min(cols), max(cols)
        if r1 - r0 + 1 > 3 or c1 - c0 + 1 > 3:
            raise ValueError("glyph exceeds a 3x3 tile")

        tile = [[0] * 3 for _ in range(3)]
        for r, c in group:
            tile[r - r0][c - c0] = grid[r][c]
        glyphs.append(
            {
                "tile": tile,
                "center_r": (r0 + r1) / 2,
                "center_c": (c0 + c1) / 2,
            }
        )

    by_height = sorted(glyphs, key=lambda item: (item["center_r"], item["center_c"]))
    upper = sorted(by_height[:2], key=lambda item: item["center_c"])
    lower = sorted(by_height[2:], key=lambda item: item["center_c"])

    result = [[0] * 7 for _ in range(7)]
    for row_group, out_r in ((upper, 0), (lower, 4)):
        for glyph, out_c in zip(row_group, (0, 4)):
            for dr in range(3):
                for dc in range(3):
                    result[out_r + dr][out_c + dc] = glyph["tile"][dr][dc]
    return result
