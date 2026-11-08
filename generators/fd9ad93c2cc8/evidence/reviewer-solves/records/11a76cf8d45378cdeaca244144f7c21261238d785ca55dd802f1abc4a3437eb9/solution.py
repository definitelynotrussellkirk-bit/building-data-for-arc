def solve(grid):
    """Find exact copies of the left-hand stencil in the field to its right.

    The solid vertical stripe separates a small reference pattern from the
    search field.  Return the field's shape, replacing each exact reference
    copy by a single azure marker at the copy's bounding-box center.
    """
    height = len(grid)
    width = len(grid[0])

    # The separator is the only non-background column filled with one color.
    separator = next(
        c
        for c in range(width)
        if grid[0][c] != 0 and all(grid[r][c] == grid[0][c] for r in range(height))
    )

    reference_area = [row[:separator] for row in grid]
    field = [row[separator + 1 :] for row in grid]

    foreground_cells = [
        (r, c, value)
        for r, row in enumerate(reference_area)
        for c, value in enumerate(row)
        if value != 0
    ]
    top = min(r for r, _, _ in foreground_cells)
    bottom = max(r for r, _, _ in foreground_cells)
    left = min(c for _, c, _ in foreground_cells)
    right = max(c for _, c, _ in foreground_cells)
    stencil = [row[left : right + 1] for row in reference_area[top : bottom + 1]]

    stencil_h = len(stencil)
    stencil_w = len(stencil[0])
    field_h = len(field)
    field_w = len(field[0])
    output = [[0 for _ in range(field_w)] for _ in range(field_h)]

    for r0 in range(field_h - stencil_h + 1):
        for c0 in range(field_w - stencil_w + 1):
            if all(
                field[r0 + dr][c0 + dc] == stencil[dr][dc]
                for dr in range(stencil_h)
                for dc in range(stencil_w)
            ):
                output[r0 + stencil_h // 2][c0 + stencil_w // 2] = 8

    return output
