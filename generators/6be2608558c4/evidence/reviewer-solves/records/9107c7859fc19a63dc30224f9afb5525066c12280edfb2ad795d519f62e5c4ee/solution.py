from copy import deepcopy


def _shape(cells):
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    normalized = frozenset((row - min_row, col - min_col) for row, col in cells)
    height = max(row for row, _ in normalized) + 1
    width = max(col for _, col in normalized) + 1
    return normalized, height, width


def _body_components(grid):
    work = deepcopy(grid)
    for row in range(min(5, len(work))):
        for col in range(min(5, len(work[0]))):
            work[row][col] = 0

    height, width = len(work), len(work[0])
    seen = set()
    components = []
    for start_row in range(height):
        for start_col in range(width):
            if work[start_row][start_col] == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for next_row, next_col in (
                    (row - 1, col),
                    (row + 1, col),
                    (row, col - 1),
                    (row, col + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen or work[next_row][next_col] == 0:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
            components.append(cells)
    return components


def solve(grid):
    exemplar_cells = [
        (row, col)
        for row in range(min(5, len(grid)))
        for col in range(min(5, len(grid[0])))
        if grid[row][col] != 0
    ]
    exemplar, _, _ = _shape(exemplar_cells)

    matches = []
    for component in _body_components(grid):
        shape, height, width = _shape(component)
        if shape == exemplar:
            matches.append((shape, height, width))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one exemplar match, found {len(matches)}")

    shape, height, width = matches[0]
    return [
        [2 if (row, col) in shape else 0 for col in range(width)]
        for row in range(height)
    ]
