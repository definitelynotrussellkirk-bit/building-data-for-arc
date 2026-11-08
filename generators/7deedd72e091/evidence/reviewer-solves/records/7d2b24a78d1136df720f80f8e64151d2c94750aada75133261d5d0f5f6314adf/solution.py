"""Compare the full binary panel masks up to quarter-turn rotation."""


def _rotate_clockwise(mask):
    return tuple(tuple(row) for row in zip(*mask[::-1]))


def _rotation_key(mask):
    rotations = []
    for _ in range(4):
        rotations.append(mask)
        mask = _rotate_clockwise(mask)
    return min(rotations)


def solve(grid):
    """Return an 8/0 matrix showing which input panels match geometrically."""
    if not grid or not grid[0]:
        return []

    width = len(grid[0])
    separators = {
        column
        for column in range(width)
        if all(row[column] == 9 for row in grid)
    }
    panels = []
    start = None
    for column in range(width + 1):
        boundary = column == width or column in separators
        if boundary and start is not None:
            panels.append(
                tuple(
                    tuple(int(value != 0) for value in row[start:column])
                    for row in grid
                )
            )
            start = None
        elif not boundary and start is None:
            start = column

    keys = [_rotation_key(panel) for panel in panels]
    return [[8 if left == right else 0 for right in keys] for left in keys]
