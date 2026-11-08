"""Visible-example solution for the assigned blind ARC puzzle."""


def _normalize(points):
    min_row = min(row for row, _ in points)
    min_col = min(col for _, col in points)
    return frozenset((row - min_row, col - min_col) for row, col in points)


def _free_shape_signature(points):
    """Canonicalize a shape over the eight square-grid symmetries."""
    points = set(points)
    variants = []
    for reflected in (False, True):
        transformed = {(row, -col) for row, col in points} if reflected else set(points)
        for turns in range(4):
            rotated = set(transformed)
            for _ in range(turns):
                rotated = {(col, -row) for row, col in rotated}
            variants.append(tuple(sorted(_normalize(rotated))))
    return min(variants)


def solve(grid):
    """Build the color/shape equivalence table encoded by the right-edge key."""
    height = len(grid)
    width = len(grid[0])

    # The isolated nonzero cells in the final column give the table order.
    colors = [grid[row][width - 1] for row in range(height) if grid[row][width - 1] != 0]

    signatures = {}
    for color in colors:
        points = {
            (row, col)
            for row in range(height)
            for col in range(width - 1)
            if grid[row][col] == color
        }
        signatures[color] = _free_shape_signature(points)

    block_count = len(colors) + 1
    side = block_count * 2 + (block_count - 1)
    output = [[0 for _ in range(side)] for _ in range(side)]

    def paint(block_row, block_col, color):
        top = block_row * 3
        left = block_col * 3
        for row in (top, top + 1):
            for col in (left, left + 1):
                output[row][col] = color

    for index, color in enumerate(colors, start=1):
        paint(0, index, color)
        paint(index, 0, color)

    for row_index, row_color in enumerate(colors, start=1):
        for col_index, col_color in enumerate(colors, start=1):
            if row_index == col_index:
                value = 0
            elif signatures[row_color] == signatures[col_color]:
                value = 2
            else:
                value = 5
            paint(row_index, col_index, value)

    return output
