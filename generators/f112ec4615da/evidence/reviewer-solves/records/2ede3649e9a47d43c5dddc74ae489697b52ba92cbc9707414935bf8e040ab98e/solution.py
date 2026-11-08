def solve(grid):
    """Overlay the four equal quadrants using the learned priority order."""
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        raise ValueError("grid must be a non-empty rectangular list of rows")
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    height = len(grid)
    if height % 2 or width % 2:
        raise ValueError("grid dimensions must both be even")

    half_h = height // 2
    half_w = width // 2
    output = [[0 for _ in range(half_w)] for _ in range(half_h)]

    for row in range(half_h):
        for col in range(half_w):
            top_left = grid[row][col]
            top_right = grid[row][col + half_w]
            bottom_left = grid[row + half_h][col]
            bottom_right = grid[row + half_h][col + half_w]

            # The visible examples establish this precedence for overlapping
            # nonzero cells: top-right, bottom-left, bottom-right, top-left.
            output[row][col] = (
                top_right
                if top_right != 0
                else bottom_left
                if bottom_left != 0
                else bottom_right
                if bottom_right != 0
                else top_left
            )

    return output
