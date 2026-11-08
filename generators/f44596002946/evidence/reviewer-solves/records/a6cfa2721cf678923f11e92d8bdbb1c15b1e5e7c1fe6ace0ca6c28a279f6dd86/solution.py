from collections import defaultdict


def solve(grid):
    """Connect each exactly-two, axis-aligned nonzero color pair.

    Segments are rendered in ascending color order.  Therefore, when two
    segments cross, the numerically larger color remains at the intersection,
    matching both visible crossing examples.
    """
    result = [row[:] for row in grid]
    positions = defaultdict(list)

    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                positions[color].append((row_index, column_index))

    for color in sorted(positions):
        points = positions[color]
        if len(points) != 2:
            continue

        (r1, c1), (r2, c2) = points
        if r1 == r2:
            for column_index in range(min(c1, c2), max(c1, c2) + 1):
                result[r1][column_index] = color
        elif c1 == c2:
            for row_index in range(min(r1, r2), max(r1, r2) + 1):
                result[row_index][c1] = color

    return result
