def solve(grid):
    """Stamp transformed copies of the color-4 template at colored anchors.

    The tight bounding box of all 4-valued cells is the template.  Each
    non-background anchor requests one copy whose top-left corner is the anchor:
    color 1 keeps the template, color 2 mirrors it left/right, and color 3 mirrors
    it top/bottom.  The source template and anchors disappear from the output.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]

    template_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 4
    ]
    if not template_cells:
        return output

    top = min(row for row, _ in template_cells)
    bottom = max(row for row, _ in template_cells)
    left = min(col for _, col in template_cells)
    right = max(col for _, col in template_cells)
    template_height = bottom - top + 1
    template_width = right - left + 1
    template = [
        [grid[top + row][left + col] == 4 for col in range(template_width)]
        for row in range(template_height)
    ]

    for anchor_row, values in enumerate(grid):
        for anchor_col, marker in enumerate(values):
            if marker not in (1, 2, 3):
                continue

            for row in range(template_height):
                for col in range(template_width):
                    source_row = template_height - 1 - row if marker == 3 else row
                    source_col = template_width - 1 - col if marker == 2 else col
                    if not template[source_row][source_col]:
                        continue

                    out_row = anchor_row + row
                    out_col = anchor_col + col
                    if 0 <= out_row < height and 0 <= out_col < width:
                        output[out_row][out_col] = 4

    return output
