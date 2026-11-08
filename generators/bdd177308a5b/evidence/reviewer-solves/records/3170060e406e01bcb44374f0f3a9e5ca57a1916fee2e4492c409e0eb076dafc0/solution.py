from collections import deque


def _components(grid):
    """Return 4-connected non-background monochrome components."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            cells = []
            queue = deque([(row, col)])
            seen.add((row, col))
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

            result.append((color, tuple(cells)))

    return result


def _normalized(cells):
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return frozenset((row - min_row, col - min_col) for row, col in cells)


def solve(grid):
    """Recolor the translated copy of the object framed by the color-5 L."""
    output = [row[:] for row in grid]
    components = _components(grid)

    frame_candidates = [cells for color, cells in components if color == 5]
    if not frame_candidates:
        raise ValueError("expected a color-5 frame")
    frame = max(frame_candidates, key=len)

    min_row = min(row for row, _ in frame)
    max_row = max(row for row, _ in frame)
    min_col = min(col for _, col in frame)
    max_col = max(col for _, col in frame)

    row_counts = {
        row: sum(cell_row == row for cell_row, _ in frame)
        for row in range(min_row, max_row + 1)
    }
    col_counts = {
        col: sum(cell_col == col for _, cell_col in frame)
        for col in range(min_col, max_col + 1)
    }
    horizontal_arm_row = max(row_counts, key=row_counts.get)
    vertical_arm_col = max(col_counts, key=col_counts.get)

    interior_rows = (
        range(min_row, horizontal_arm_row)
        if horizontal_arm_row == max_row
        else range(horizontal_arm_row + 1, max_row + 1)
    )
    interior_cols = (
        range(min_col, vertical_arm_col)
        if vertical_arm_col == max_col
        else range(vertical_arm_col + 1, max_col + 1)
    )
    interior = {(row, col) for row in interior_rows for col in interior_cols}

    exemplar_candidates = [
        (color, cells)
        for color, cells in components
        if color not in (0, 5) and cells and all(cell in interior for cell in cells)
    ]
    if len(exemplar_candidates) != 1:
        raise ValueError(f"expected one framed exemplar, found {len(exemplar_candidates)}")

    exemplar_color, exemplar_cells = exemplar_candidates[0]
    exemplar_shape = _normalized(exemplar_cells)
    exemplar_set = set(exemplar_cells)

    matches = [
        cells
        for color, cells in components
        if color not in (0, 5)
        and set(cells) != exemplar_set
        and _normalized(cells) == exemplar_shape
    ]
    if not matches:
        raise ValueError("expected a translated copy of the framed exemplar")

    for cells in matches:
        for row, col in cells:
            output[row][col] = 5

    return output
