from itertools import combinations


def solve(grid):
    """Rotate the blue/azure square according to the yellow L-shaped cue."""
    height = len(grid)
    width = len(grid[0])
    out = [row[:] for row in grid]

    object_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in (1, 8)
    ]
    if not object_cells:
        return out

    top = min(r for r, _ in object_cells)
    bottom = max(r for r, _ in object_cells)
    left = min(c for _, c in object_cells)
    right = max(c for _, c in object_cells)

    square = [row[left : right + 1] for row in grid[top : bottom + 1]]
    if len(square) != len(square[0]):
        raise ValueError("the colored object must be square")

    yellow = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 4
    ]

    outer_corners = {
        "NW": (top - 1, left - 1),
        "NE": (top - 1, right + 1),
        "SE": (bottom + 1, right + 1),
        "SW": (bottom + 1, left - 1),
    }
    start_labels = [name for name, point in outer_corners.items() if point in yellow]
    if len(start_labels) != 1:
        raise ValueError("expected one yellow marker at an outer object corner")
    start = start_labels[0]
    start_point = outer_corners[start]

    cue = [point for point in yellow if point != start_point]
    if len(cue) != 3:
        raise ValueError("expected a three-point L cue and one object marker")

    corner = horizontal_endpoint = None
    for p, q in combinations(cue, 2):
        if p[0] != q[0]:
            continue
        third = next(point for point in cue if point not in (p, q))
        if p[1] == third[1]:
            corner, horizontal_endpoint = p, q
            break
        if q[1] == third[1]:
            corner, horizontal_endpoint = q, p
            break
    if corner is None or horizontal_endpoint is None:
        raise ValueError("yellow cue is not an axis-aligned L")

    clockwise = horizontal_endpoint[1] < corner[1]

    # Remove all instruction markers before drawing the transformed scene.
    for r, c in yellow:
        out[r][c] = 0

    n = len(square)
    if clockwise:
        rotated = [[square[n - 1 - r][c] for r in range(n)] for c in range(n)]
    else:
        rotated = [[square[r][n - 1 - c] for r in range(n)] for c in range(n)]

    for r in range(n):
        for c in range(n):
            out[top + r][left + c] = rotated[r][c]

    order = ["NW", "NE", "SE", "SW"]
    index = order.index(start)
    destination = order[(index + 1) % 4] if clockwise else order[(index - 1) % 4]
    marker_r, marker_c = outer_corners[destination]
    if not (0 <= marker_r < height and 0 <= marker_c < width):
        raise ValueError("destination marker falls outside the grid")
    out[marker_r][marker_c] = 4
    return out
