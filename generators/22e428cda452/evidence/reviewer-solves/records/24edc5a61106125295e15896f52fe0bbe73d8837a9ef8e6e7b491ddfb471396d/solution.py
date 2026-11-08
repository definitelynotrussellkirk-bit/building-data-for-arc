from collections import Counter


def solve(grid):
    """Replace colored corner markers with their inward-facing glyphs."""
    height = len(grid)
    width = len(grid[0])
    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    output = [[background for _ in range(width)] for _ in range(height)]

    corners = {
        "top_left": (0, 0),
        "top_right": (0, width - 1),
        "bottom_left": (height - 1, 0),
        "bottom_right": (height - 1, width - 1),
    }

    top_glyphs = {
        "top_left": ((1, 1), (1, 2), (2, 1), (2, 2)),
        "top_right": ((1, width - 3), (1, width - 2), (2, width - 3), (2, width - 2)),
    }
    bottom_glyphs = {
        "bottom_left": ((height - 4, 2), (height - 3, 2), (height - 2, 3)),
        "bottom_right": ((height - 4, width - 3), (height - 3, width - 3), (height - 2, width - 4)),
    }

    for name, (row, col) in corners.items():
        color = grid[row][col]
        if color == background:
            continue
        cells = top_glyphs[name] if name in top_glyphs else bottom_glyphs[name]
        for out_row, out_col in cells:
            output[out_row][out_col] = color

    return output
