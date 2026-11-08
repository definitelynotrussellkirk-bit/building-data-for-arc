"""Visible-example solution for task 5fdbbb5a53ef."""


def _is_frame(grid, row, col):
    """Return whether (row, col) is the top-left of a color-9 5x5 frame."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    if row + 5 > height or col + 5 > width:
        return False
    if any(grid[row][col + dc] != 9 for dc in range(5)):
        return False
    if any(grid[row + 4][col + dc] != 9 for dc in range(5)):
        return False
    return all(grid[row + dr][col] == 9 and grid[row + dr][col + 4] == 9 for dr in range(1, 4))


def _normalize(cells):
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return frozenset((row - min_row, col - min_col) for row, col in cells)


def _rotate(cells):
    return [(col, -row) for row, col in cells]


def _rotation_class(cells):
    variants = []
    current = list(cells)
    for _ in range(4):
        variants.append(tuple(sorted(_normalize(current))))
        current = _rotate(current)
    return min(variants)


def _panel(grid, row, col):
    colored = [
        (dr, dc, grid[row + 1 + dr][col + 1 + dc])
        for dr in range(3)
        for dc in range(3)
        if grid[row + 1 + dr][col + 1 + dc] not in (0, 9)
    ]
    if not colored:
        raise ValueError("empty framed panel")
    colors = {value for _, _, value in colored}
    if len(colors) != 1:
        raise ValueError("a panel must use one shape color")
    cells = [(dr, dc) for dr, dc, _ in colored]
    return _rotation_class(cells), colors.pop()


def solve(grid):
    """Build the left-by-top matrix of shape/color relationships.

    Output codes inferred from the visible examples:
      8: same shape up to rotation and same color
      6: same shape up to rotation only
      3: same color only
      0: neither
    """
    if not grid or not grid[0]:
        return []

    frames = [
        (row, col)
        for row in range(len(grid) - 4)
        for col in range(len(grid[0]) - 4)
        if _is_frame(grid, row, col)
    ]
    if not frames:
        return []

    top_row = min(row for row, _ in frames)
    left_col = min(col for _, col in frames)
    top_frames = sorted((pos for pos in frames if pos[0] == top_row), key=lambda pos: pos[1])
    left_frames = sorted(
        (pos for pos in frames if pos[1] == left_col and pos[0] > top_row),
        key=lambda pos: pos[0],
    )

    top_panels = [_panel(grid, row, col) for row, col in top_frames]
    left_panels = [_panel(grid, row, col) for row, col in left_frames]

    output = []
    for left_shape, left_color in left_panels:
        out_row = []
        for top_shape, top_color in top_panels:
            same_shape = left_shape == top_shape
            same_color = left_color == top_color
            if same_shape and same_color:
                value = 8
            elif same_shape:
                value = 6
            elif same_color:
                value = 3
            else:
                value = 0
            out_row.append(value)
        output.append(out_row)
    return output
