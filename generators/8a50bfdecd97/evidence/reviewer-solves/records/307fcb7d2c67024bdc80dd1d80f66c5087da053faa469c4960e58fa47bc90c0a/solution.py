def solve(grid):
    """Move the non-{4,7} bitmap into the missing bracket-defined corner."""
    height = len(grid)
    width = len(grid[0])
    background = 7
    bracket_color = 4

    # Find the two orthogonally connected color-4 brackets.
    seen = set()
    brackets = []
    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] != bracket_color:
                continue
            if (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row, next_col = row + drow, col + dcol
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != bracket_color:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))

            top = min(row for row, _ in cells)
            bottom = max(row for row, _ in cells)
            left = min(col for _, col in cells)
            right = max(col for _, col in cells)
            top_is_solid = all(grid[top][col] == bracket_color for col in range(left, right + 1))
            bottom_is_solid = all(
                grid[bottom][col] == bracket_color for col in range(left, right + 1)
            )
            orientation = "top" if top_is_solid and not bottom_is_solid else "bottom"
            side = "left" if (left + right) / 2 < (width - 1) / 2 else "right"
            brackets.append(
                {
                    "top": top,
                    "bottom": bottom,
                    "left": left,
                    "right": right,
                    "orientation": orientation,
                    "side": side,
                }
            )

    movable_colors = {
        value
        for row in grid
        for value in row
        if value not in (background, bracket_color)
    }
    movable_color = next(iter(movable_colors))
    shape_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == movable_color
    ]
    source_top = min(row for row, _ in shape_cells)
    source_bottom = max(row for row, _ in shape_cells)
    source_left = min(col for _, col in shape_cells)
    source_right = max(col for _, col in shape_cells)
    shape_height = source_bottom - source_top + 1
    shape_width = source_right - source_left + 1
    offsets = {(row - source_top, col - source_left) for row, col in shape_cells}

    source_side = (
        "left"
        if (source_left + source_right) / 2 < (width - 1) / 2
        else "right"
    )
    row_bracket = next(bracket for bracket in brackets if bracket["side"] == source_side)
    column_bracket = next(bracket for bracket in brackets if bracket["side"] != source_side)

    if row_bracket["orientation"] == "top":
        destination_top = row_bracket["top"]
    else:
        destination_top = row_bracket["bottom"] - shape_height + 1

    # The opposite-side bracket supplies an open interior column interval.
    # Align the bitmap toward that bracket's outer side when the interval is wider.
    if column_bracket["side"] == "left":
        destination_left = column_bracket["left"] + 1
    else:
        destination_left = column_bracket["right"] - shape_width

    result = [row[:] for row in grid]
    for row, col in shape_cells:
        result[row][col] = background
    for drow, dcol in offsets:
        result[destination_top + drow][destination_left + dcol] = movable_color
    return result
