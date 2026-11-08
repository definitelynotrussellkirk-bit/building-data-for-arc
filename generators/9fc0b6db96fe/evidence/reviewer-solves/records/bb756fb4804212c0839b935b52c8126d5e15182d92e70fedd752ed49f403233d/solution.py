from collections import deque


def _components(grid):
    """Return 4-connected nonzero components from rows 2 onward."""
    body = grid[2:]
    height, width = len(body), len(body[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if body[row][col] == 0 or (row, col) in seen:
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
                    if (next_row, next_col) in seen or body[next_row][next_col] == 0:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))
            components.append(cells)
    return body, components


def _crop(body, cells):
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    occupied = set(cells)
    return [
        [body[row][col] if (row, col) in occupied else 0 for col in range(left, right + 1)]
        for row in range(top, bottom + 1)
    ]


def _transform(piece, key):
    if key == 1:  # identity
        return [row[:] for row in piece]
    if key == 2:  # clockwise quarter-turn
        return [list(row) for row in zip(*piece[::-1])]
    if key == 3:  # half-turn
        return [row[::-1] for row in piece[::-1]]
    if key == 4:  # left-right reflection
        return [row[::-1] for row in piece]
    raise ValueError(f"unsupported transform key: {key}")


def solve(grid):
    key = grid[0][0]
    legend = [value for value in grid[0][1:] if value != 0]
    body, components = _components(grid)

    pieces = []
    for color in legend:
        cells = next(
            component
            for component in components
            if body[component[0][0]][component[0][1]] == color
        )
        pieces.append(_transform(_crop(body, cells), key))

    output_height = max(len(piece) for piece in pieces)
    output_width = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    output = [[0] * output_width for _ in range(output_height)]
    left = 0
    for piece in pieces:
        for row, values in enumerate(piece):
            for col, value in enumerate(values):
                if value != 0:
                    output[row][left + col] = value
        left += len(piece[0]) + 1
    return output
