"""Visible-only solution for ARC task 9e80ef661ecc."""

NEIGHBORS = ((1, 0), (-1, 0), (0, 1), (0, -1))
HOLE_COLORS = (2, 3, 4, 6, 9)


def _components(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            cells = []
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for row_delta, col_delta in NEIGHBORS:
                    next_row = current_row + row_delta
                    next_col = current_col + col_delta
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))

            yield cells


def _hole_count(cells):
    min_row = min(row for row, _ in cells)
    max_row = max(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    max_col = max(col for _, col in cells)

    # Translate the object into a local mask with one cell of exterior padding.
    occupied = {
        (row - min_row + 1, col - min_col + 1)
        for row, col in cells
    }
    height = max_row - min_row + 3
    width = max_col - min_col + 3

    visited = {(0, 0)}
    stack = [(0, 0)]
    while stack:
        row, col = stack.pop()
        for row_delta, col_delta in NEIGHBORS:
            next_row = row + row_delta
            next_col = col + col_delta
            if not (0 <= next_row < height and 0 <= next_col < width):
                continue
            position = (next_row, next_col)
            if position in occupied or position in visited:
                continue
            visited.add(position)
            stack.append(position)

    holes = 0
    for row in range(height):
        for col in range(width):
            start = (row, col)
            if start in occupied or start in visited:
                continue

            holes += 1
            visited.add(start)
            stack = [start]
            while stack:
                current_row, current_col = stack.pop()
                for row_delta, col_delta in NEIGHBORS:
                    next_row = current_row + row_delta
                    next_col = current_col + col_delta
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    position = (next_row, next_col)
                    if position in occupied or position in visited:
                        continue
                    visited.add(position)
                    stack.append(position)

    return holes


def solve(grid):
    output = [row[:] for row in grid]
    for cells in _components(grid):
        holes = _hole_count(cells)
        color = HOLE_COLORS[min(holes, len(HOLE_COLORS) - 1)]
        for row, col in cells:
            output[row][col] = color
    return output
