def solve(grid):
    """Extend the central axes of every solid nonzero square.

    Each square paints its own color along its middle row/column.  Even-sided
    squares have two middle rows and two middle columns.  If axes from squares
    of different colors reach the same cell, the colors cancel to background.
    Cells reached by no axis are left unchanged.
    """
    height = len(grid)
    width = len(grid[0])
    seen = set()
    emitters = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            component = []
            while stack:
                current_row, current_col = stack.pop()
                component.append((current_row, current_col))
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
                    stack.append((next_row, next_col))

            rows = [cell_row for cell_row, _ in component]
            cols = [cell_col for _, cell_col in component]
            top, bottom = min(rows), max(rows)
            left, right = min(cols), max(cols)
            side_y = bottom - top + 1
            side_x = right - left + 1

            if side_y < 2 or side_y != side_x:
                continue
            if len(component) != side_y * side_x:
                continue

            middle_rows = set(range(top + (side_y - 1) // 2, top + side_y // 2 + 1))
            middle_cols = set(range(left + (side_x - 1) // 2, left + side_x // 2 + 1))
            emitters.append((color, middle_rows, middle_cols))

    result = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            colors = {
                color
                for color, middle_rows, middle_cols in emitters
                if row in middle_rows or col in middle_cols
            }
            if len(colors) == 1:
                result[row][col] = next(iter(colors))
            elif len(colors) > 1:
                result[row][col] = 0

    return result
