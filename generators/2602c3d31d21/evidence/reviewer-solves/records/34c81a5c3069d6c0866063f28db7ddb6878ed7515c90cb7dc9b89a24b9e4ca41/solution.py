"""Visible-example solution for blind task 2602c3d31d21."""


def _canonical_shape(cells):
    """Canonicalize a finite cell set under translation, rotation and reflection."""
    variants = []
    for reflected in (False, True):
        for rotations in range(4):
            transformed = []
            for row, col in cells:
                x, y = row, (-col if reflected else col)
                for _ in range(rotations):
                    x, y = y, -x
                transformed.append((x, y))
            min_row = min(row for row, _ in transformed)
            min_col = min(col for _, col in transformed)
            variants.append(
                tuple(sorted((row - min_row, col - min_col)
                             for row, col in transformed))
            )
    return min(variants)


def solve(grid):
    """Build the labelled shape-congruence table encoded by the input."""
    nonzero = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not nonzero:
        return []

    # The rightmost occupied column is a top-to-bottom legend.  Remove those
    # singleton labels before extracting each colored shape.
    legend_col = max(col for _, col, _ in nonzero)
    colors = [
        grid[row][legend_col]
        for row in range(len(grid))
        if grid[row][legend_col] != 0
    ]

    shapes = {}
    for color in colors:
        cells = [
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == color and col != legend_col
        ]
        shapes[color] = _canonical_shape(cells)

    n = len(colors)
    size = 3 * n + 2
    output = [[0 for _ in range(size)] for _ in range(size)]

    # Two-cell-square legend blocks along the top and left.
    for index, color in enumerate(colors):
        start = 3 + 3 * index
        for delta in (0, 1):
            output[delta][start] = color
            output[delta][start + 1] = color
            output[start][delta] = color
            output[start + 1][delta] = color

    # A 2x2 value block for every pair: black diagonal, red (2) when the
    # shapes are congruent, gray (5) otherwise.  Zero separator rows/columns
    # remain between blocks.
    for row_index, row_color in enumerate(colors):
        row_start = 3 + 3 * row_index
        for col_index, col_color in enumerate(colors):
            col_start = 3 + 3 * col_index
            if row_index == col_index:
                value = 0
            elif shapes[row_color] == shapes[col_color]:
                value = 2
            else:
                value = 5
            for dr in (0, 1):
                for dc in (0, 1):
                    output[row_start + dr][col_start + dc] = value

    return output
