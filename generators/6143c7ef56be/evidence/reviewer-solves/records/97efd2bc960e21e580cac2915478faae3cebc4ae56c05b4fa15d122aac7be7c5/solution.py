def solve(grid):
    """Move the four quadrant marker colors into the 2x2 block of 8s."""
    height = len(grid)
    width = len(grid[0])

    eights = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 8
    ]
    if len(eights) != 4:
        raise ValueError("expected exactly four cells of color 8")

    top = min(row for row, _ in eights)
    bottom = max(row for row, _ in eights)
    left = min(col for _, col in eights)
    right = max(col for _, col in eights)
    if bottom != top + 1 or right != left + 1 or set(eights) != {
        (top, left),
        (top, right),
        (bottom, left),
        (bottom, right),
    }:
        raise ValueError("the color-8 cells must form a 2x2 block")

    markers = [
        (row, col, value)
        for row in range(height)
        for col in range(width)
        if (value := grid[row][col]) not in (0, 8)
    ]
    if len(markers) != 4:
        raise ValueError("expected exactly four colored marker cells")

    result = [[0 for _ in range(width)] for _ in range(height)]
    occupied_quadrants = set()
    for row, col, value in markers:
        out_row = top if row < top else bottom
        out_col = left if col < left else right
        quadrant = (out_row, out_col)
        if quadrant in occupied_quadrants:
            raise ValueError("expected one marker in each quadrant around the block")
        occupied_quadrants.add(quadrant)
        result[out_row][out_col] = value

    return result
