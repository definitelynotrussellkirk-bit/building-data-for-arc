from collections import defaultdict, deque


def _components(grid):
    """Return cropped nonzero 4-connected components as 0/1 tuples."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            points = []

            while queue:
                current_row, current_col = queue.popleft()
                points.append((current_row, current_col))
                for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if grid[next_row][next_col] == 0 or (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            min_row = min(point[0] for point in points)
            max_row = max(point[0] for point in points)
            min_col = min(point[1] for point in points)
            max_col = max(point[1] for point in points)
            point_set = set(points)
            cropped = tuple(
                tuple(
                    1 if (source_row, source_col) in point_set else 0
                    for source_col in range(min_col, max_col + 1)
                )
                for source_row in range(min_row, max_row + 1)
            )
            components.append(cropped)

    return components


def _rotate_clockwise(shape):
    return tuple(tuple(row) for row in zip(*shape[::-1]))


def _rotations(shape):
    result = []
    current = shape
    for _ in range(4):
        if current not in result:
            result.append(current)
        current = _rotate_clockwise(current)
    return result


def _rotation_key(shape):
    # Canonicalize a rotation class independently of the orientation used for output.
    return min(_rotations(shape))


def _output_orientation(shape):
    # The examples orient the extracted shape as horizontally as possible.  When
    # dimensions tie, choose the row-major orientation with occupied cells earliest.
    return max(
        _rotations(shape),
        key=lambda candidate: (
            -len(candidate),
            len(candidate[0]),
            tuple(value for row in candidate for value in row),
        ),
    )


def solve(grid):
    components = _components(grid)
    by_rotation_class = defaultdict(list)
    for component in components:
        by_rotation_class[_rotation_key(component)].append(component)

    repeated_classes = [
        members for members in by_rotation_class.values() if len(members) >= 2
    ]
    if not repeated_classes:
        raise ValueError("No repeated component shape under rotation")

    # The task examples have exactly one repeated rotation class.  Prefer the most
    # repeated class, then the one with the most cells as a deterministic fallback.
    selected = max(
        repeated_classes,
        key=lambda members: (
            len(members),
            sum(sum(row) for row in members[0]),
        ),
    )[0]
    oriented = _output_orientation(selected)
    return [[8 if value else 0 for value in row] for row in oriented]
