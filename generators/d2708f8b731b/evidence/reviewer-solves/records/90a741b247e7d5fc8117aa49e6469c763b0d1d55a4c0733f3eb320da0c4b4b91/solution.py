"""Visible-only solver for the assigned ARC puzzle.

The non-blue singleton colors label nearby blue reference shapes.  Every other
blue connected component with the same translated shape is recolored with that
label, while the labelled reference component stays blue.
"""


def _components(grid, color):
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    unseen = {
        (r, c)
        for r in range(rows)
        for c in range(cols)
        if grid[r][c] == color
    }
    result = []
    while unseen:
        start = unseen.pop()
        stack = [start]
        cells = [start]
        while stack:
            r, c = stack.pop()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in unseen:
                    unseen.remove((nr, nc))
                    stack.append((nr, nc))
                    cells.append((nr, nc))
        result.append(frozenset(cells))
    return result


def _shape(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return frozenset((r - min_r, c - min_c) for r, c in cells)


def _distance(point, cells):
    pr, pc = point
    return min(abs(pr - r) + abs(pc - c) for r, c in cells)


def solve(grid):
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    blue_components = _components(grid, 1)
    markers = [
        (grid[r][c], (r, c))
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] not in (0, 1)
    ]

    # Each colored singleton is placed nearest to the blue example whose shape
    # it names.  Record both the named shape and the specific example so that
    # the example itself remains unchanged.
    color_for_shape = {}
    reference_components = set()
    for marker_color, marker_pos in markers:
        reference_index = min(
            range(len(blue_components)),
            key=lambda i: (_distance(marker_pos, blue_components[i]), i),
        )
        reference_components.add(reference_index)
        color_for_shape[_shape(blue_components[reference_index])] = marker_color

    output = [row[:] for row in grid]
    for index, cells in enumerate(blue_components):
        if index in reference_components:
            continue
        replacement = color_for_shape.get(_shape(cells))
        if replacement is None:
            continue
        for r, c in cells:
            output[r][c] = replacement
    return output
