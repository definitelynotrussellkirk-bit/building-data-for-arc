def solve(grid):
    """Stamp the color-2 template at every colored marker.

    The template is normalized to the top-left corner of its bounding box.
    Each singleton/cell of colors 3..9 is an anchor and supplies the copy color.
    The source template is omitted, out-of-bounds copy cells are clipped, and
    processing colors in ascending order makes higher colors win overlaps.
    """
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    template = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    ]
    if not template:
        return [[0] * width for _ in range(height)]

    top = min(row for row, _col in template)
    left = min(col for _row, col in template)
    offsets = sorted((row - top, col - left) for row, col in template)

    output = [[0] * width for _ in range(height)]
    for color in range(3, 10):
        anchors = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == color
        ]
        for anchor_row, anchor_col in anchors:
            for delta_row, delta_col in offsets:
                row = anchor_row + delta_row
                col = anchor_col + delta_col
                if 0 <= row < height and 0 <= col < width:
                    output[row][col] = color
    return output
