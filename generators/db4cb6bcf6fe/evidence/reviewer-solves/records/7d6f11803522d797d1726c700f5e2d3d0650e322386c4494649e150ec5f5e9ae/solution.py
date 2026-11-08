"""Compare translated convex hulls of same-colored point patterns."""


def _hull_signature(points):
    """Return the convex hull after translating its bounding box to the origin."""
    min_row = min(row for row, col in points)
    min_col = min(col for row, col in points)
    points = sorted({(row - min_row, col - min_col) for row, col in points})
    if len(points) <= 1:
        return tuple(points)

    def cross(origin, a, b):
        return ((a[0] - origin[0]) * (b[1] - origin[1])
                - (a[1] - origin[1]) * (b[0] - origin[0]))

    lower = []
    for point in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper = []
    for point in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return tuple(sorted(lower[:-1] + upper[:-1]))


def solve(grid):
    points_by_color = {}
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color != 0:
                points_by_color.setdefault(color, []).append((row, col))
    colors = sorted(points_by_color)
    hulls = [_hull_signature(points_by_color[color]) for color in colors]
    return [
        [5 if i == j else 8 if hulls[i] == hulls[j] else 0
         for j in range(len(colors))]
        for i in range(len(colors))
    ]
