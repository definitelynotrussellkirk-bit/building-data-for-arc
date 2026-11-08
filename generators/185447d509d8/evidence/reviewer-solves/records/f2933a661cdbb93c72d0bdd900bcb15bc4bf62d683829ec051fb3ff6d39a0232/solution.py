from collections import deque


def _normalize(cells):
    cells = tuple(cells)
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _rotate(shape):
    shape = _normalize(shape)
    max_row = max(row for row, _ in shape)
    return _normalize((col, max_row - row) for row, col in shape)


def _flip(shape):
    shape = _normalize(shape)
    max_col = max(col for _, col in shape)
    return _normalize((row, max_col - col) for row, col in shape)


def _dihedral_forms(shape):
    current = _normalize(shape)
    forms = set()
    for _ in range(4):
        forms.add(current)
        forms.add(_flip(current))
        current = _rotate(current)
    return forms


def _components(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []
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
                for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
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
            bbox_key = (
                min(cell_row for cell_row, _ in cells),
                min(cell_col for _, cell_col in cells),
            )
            components.append((bbox_key, _normalize(cells)))
    components.sort(key=lambda item: item[0])
    return [shape for _, shape in components]


def solve(grid):
    shapes = _components(grid)
    return [
        [2 if right in _dihedral_forms(left) else 0 for right in shapes]
        for left in shapes
    ]
