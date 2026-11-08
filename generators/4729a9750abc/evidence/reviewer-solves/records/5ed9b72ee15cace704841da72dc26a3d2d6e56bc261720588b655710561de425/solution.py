"""Solver inferred from the visible examples in challenge.json."""

from collections import deque


_NEIGHBORS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _same_color_components(grid, *, color=None, ignore_zero=False):
    """Return (value, cells) 4-connected components in row-major order."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if (row, col) in seen:
                continue
            if color is not None and value != color:
                continue
            if ignore_zero and value == 0:
                continue

            seen.add((row, col))
            queue = deque([(row, col)])
            cells = []
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for delta_row, delta_col in _NEIGHBORS:
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != value:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            components.append((value, cells))

    return components


def _bounding_box(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), max(rows), min(cols), max(cols)


def _crop_component(value, cells):
    top, bottom, left, right = _bounding_box(cells)
    cropped = [[0 for _ in range(right - left + 1)] for _ in range(bottom - top + 1)]
    for row, col in cells:
        cropped[row - top][col - left] = value
    return cropped


def _rotate_clockwise(piece):
    return [list(row) for row in zip(*piece[::-1])]


def _transform(piece, key):
    if key == 3:  # identity
        return [row[:] for row in piece]
    if key == 4:  # clockwise quarter-turn
        return _rotate_clockwise(piece)
    if key == 5:  # left-right reflection
        return [row[::-1] for row in piece]
    if key == 6:  # half-turn
        return [row[::-1] for row in piece[::-1]]
    raise ValueError(f"unknown transform key: {key}")


def _single_key(values, *, kind):
    keys = [value for value in values if value != 0]
    if len(keys) != 1:
        raise ValueError(f"expected one {kind} key, found {keys}")
    return keys[0]


def solve(grid):
    """Select, transform, and horizontally pack one object from each frame."""
    if not grid or not grid[0]:
        return []

    # Each color-9 connected component is one hollow rectangular frame.
    frames = []
    for _, frame_cells in _same_color_components(grid, color=9):
        top, bottom, left, right = _bounding_box(frame_cells)
        frames.append((left, top, bottom, right))
    frames.sort()

    pieces = []
    for left, top, bottom, right in frames:
        rank_key = _single_key(grid[top - 1][left : right + 1], kind="rank")
        transform_key = _single_key(
            [grid[row][left - 1] for row in range(top, bottom + 1)],
            kind="transform",
        )

        interior = [row[left + 1 : right] for row in grid[top + 1 : bottom]]
        objects = _same_color_components(interior, ignore_zero=True)
        objects.sort(key=lambda item: len(item[1]))

        if rank_key == 2:
            selected = objects[0]
        elif rank_key == 3:
            selected = objects[-1]
        else:
            raise ValueError(f"unknown rank key: {rank_key}")

        value, cells = selected
        piece = _crop_component(value, cells)
        pieces.append(_transform(piece, transform_key))

    if not pieces:
        return []

    output_height = max(len(piece) for piece in pieces)
    output_width = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    output = [[0 for _ in range(output_width)] for _ in range(output_height)]

    cursor = 0
    for piece in pieces:
        # Center vertically; when the difference is odd, the extra blank row is below.
        row_offset = (output_height - len(piece)) // 2
        for row, values in enumerate(piece):
            for col, value in enumerate(values):
                output[row_offset + row][cursor + col] = value
        cursor += len(piece[0]) + 1

    return output
