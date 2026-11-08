from collections import deque


def _components(grid, color):
    """Return 4-connected components for one non-background color."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            todo = deque([(row, col)])
            seen.add((row, col))
            component = []
            while todo:
                r, c = todo.popleft()
                component.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            components.append(component)
    return components


def _crop_component(component, color):
    min_row = min(r for r, _ in component)
    max_row = max(r for r, _ in component)
    min_col = min(c for _, c in component)
    max_col = max(c for _, c in component)
    cropped = [
        [0 for _ in range(max_col - min_col + 1)]
        for _ in range(max_row - min_row + 1)
    ]
    for row, col in component:
        cropped[row - min_row][col - min_col] = color
    return cropped


def solve(grid):
    if not grid or not grid[0]:
        return []

    # The first non-empty row is the left-to-right assembly key.
    key_row = next(row for row in grid if any(value != 0 for value in row))
    order = []
    for value in key_row:
        if value != 0 and value not in order:
            order.append(value)

    pieces = []
    for color in order:
        components = _components(grid, color)
        # Sparse key marks are isolated; the lower, largest component is the piece.
        component = max(
            components,
            key=lambda cells: (len(cells), min(r for r, _ in cells)),
        )
        pieces.append(_crop_component(component, color))

    output_height = max(len(piece) for piece in pieces)
    output_width = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    output = [[0 for _ in range(output_width)] for _ in range(output_height)]

    col_offset = 0
    for index, piece in enumerate(pieces):
        for row, values in enumerate(piece):
            output[row][col_offset : col_offset + len(values)] = values
        col_offset += len(piece[0])
        if index + 1 < len(pieces):
            col_offset += 1

    return output
