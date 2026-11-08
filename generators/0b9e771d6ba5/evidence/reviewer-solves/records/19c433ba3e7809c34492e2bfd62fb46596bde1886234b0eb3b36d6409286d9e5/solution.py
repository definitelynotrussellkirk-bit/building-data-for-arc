from collections import Counter


def solve(grid):
    """Complete occluded solid rectangles whose bounding boxes contain no background.

    A color is treated as an occluded rectangle when its axis-aligned bounding box
    is completely occupied by non-background cells but is not already monochrome.
    All such boxes are repainted with their owning color.  If two inferred boxes
    overlap, the box with larger area has priority (then the one with more visible
    support, then the earlier visible color), because it has the stronger extent
    witness in the visible grid.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]

    first_seen = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            first_seen.setdefault(value, (r, c))

    candidates = []
    for color in counts:
        if color == background:
            continue
        points = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        r0 = min(r for r, _ in points)
        r1 = max(r for r, _ in points)
        c0 = min(c for _, c in points)
        c1 = max(c for _, c in points)
        area = (r1 - r0 + 1) * (c1 - c0 + 1)

        # A completed rectangle needs a change and cannot bridge background.
        if area == len(points):
            continue
        if any(
            grid[r][c] == background
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
        ):
            continue

        candidates.append(
            {
                "color": color,
                "r0": r0,
                "r1": r1,
                "c0": c0,
                "c1": c1,
                "area": area,
                "support": len(points),
                "first": first_seen[color],
            }
        )

    result = [row[:] for row in grid]
    claims = {}
    for candidate in candidates:
        priority = (
            candidate["area"],
            candidate["support"],
            -candidate["first"][0],
            -candidate["first"][1],
        )
        for r in range(candidate["r0"], candidate["r1"] + 1):
            for c in range(candidate["c0"], candidate["c1"] + 1):
                if (r, c) not in claims or priority > claims[(r, c)][0]:
                    claims[(r, c)] = (priority, candidate["color"])

    for (r, c), (_, color) in claims.items():
        result[r][c] = color
    return result
