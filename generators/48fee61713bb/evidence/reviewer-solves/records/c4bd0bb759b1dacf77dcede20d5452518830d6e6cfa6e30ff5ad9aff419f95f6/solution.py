def solve(grid):
    """Decode the 7x7 block board, apply the indicated sideways gravity, and crop."""
    height = len(grid)
    width = len(grid[0])

    if all(value == 1 for value in grid[0]):
        wall = "top"
    elif all(value == 1 for value in grid[-1]):
        wall = "bottom"
    elif all(row[0] == 1 for row in grid):
        wall = "left"
    elif all(row[-1] == 1 for row in grid):
        wall = "right"
    else:
        raise ValueError("expected a solid color-1 border on one side")

    # Each logical cell is drawn as a 3x3 hollow square, with a one-cell gap.
    # A wall on the top/left shifts the first square inward by one extra cell.
    row0 = 2 if wall == "top" else 1
    col0 = 2 if wall == "left" else 1
    board = [
        [grid[row0 + 4 * row][col0 + 4 * col] for col in range(7)]
        for row in range(7)
    ]

    # The wall is an arrow shaft: gravity acts 90 degrees clockwise from it.
    direction = {
        "top": "right",
        "right": "down",
        "bottom": "left",
        "left": "up",
    }[wall]

    packed = [[0] * 7 for _ in range(7)]
    if direction in ("up", "down"):
        for col in range(7):
            values = [board[row][col] for row in range(7) if board[row][col] != 0]
            start = 0 if direction == "up" else 7 - len(values)
            for offset, value in enumerate(values):
                packed[start + offset][col] = value
    else:
        for row in range(7):
            values = [board[row][col] for col in range(7) if board[row][col] != 0]
            start = 0 if direction == "left" else 7 - len(values)
            for offset, value in enumerate(values):
                packed[row][start + offset] = value

    nonempty_rows = [row for row in range(7) if any(packed[row])]
    nonempty_cols = [col for col in range(7) if any(packed[row][col] for row in range(7))]
    if not nonempty_rows or not nonempty_cols:
        return []

    r0, r1 = nonempty_rows[0], nonempty_rows[-1]
    c0, c1 = nonempty_cols[0], nonempty_cols[-1]
    return [row[c0 : c1 + 1] for row in packed[r0 : r1 + 1]]
