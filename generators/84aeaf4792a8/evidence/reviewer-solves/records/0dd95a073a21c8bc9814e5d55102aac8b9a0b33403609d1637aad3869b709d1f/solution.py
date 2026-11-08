from collections import deque


def _components(grid):
    """Return monochromatic 4-connected components in reading order."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    parts = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            parts.append(cells)

    parts.sort(key=lambda cells: (min(row for row, _ in cells), min(col for _, col in cells)))
    return parts


def _normalize(cells):
    cells = tuple(cells)
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return frozenset((row - min_row, col - min_col) for row, col in cells)


def _rotate(cells):
    """Rotate a normalized shape clockwise, then normalize it again."""
    max_row = max(row for row, _ in cells)
    return _normalize((col, max_row - row) for row, col in cells)


def _rotation_signature(cells):
    shape = _normalize(cells)
    rotations = []
    for _ in range(4):
        rotations.append(tuple(sorted(shape)))
        shape = _rotate(shape)
    return min(rotations)


def solve(grid):
    components = _components(grid)
    signatures = [_rotation_signature(component) for component in components]
    size = len(components)

    result = [[0 for _ in range(size)] for _ in range(size)]
    for row in range(size):
        result[row][row] = 5
        for col in range(row + 1, size):
            if signatures[row] == signatures[col]:
                result[row][col] = 8
                result[col][row] = 8
    return result
