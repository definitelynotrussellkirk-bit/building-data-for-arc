def solve(grid):
    """Overlay corresponding cells of the four equal quadrants.

    Visible examples establish the nonzero priority TR > BL > BR > TL.
    """
    height = len(grid)
    width = len(grid[0])
    half_height = height // 2
    half_width = width // 2
    output = []
    for row in range(half_height):
        out_row = []
        for col in range(half_width):
            tl = grid[row][col]
            tr = grid[row][col + half_width]
            bl = grid[row + half_height][col]
            br = grid[row + half_height][col + half_width]
            out_row.append(tr or bl or br or tl)
        output.append(out_row)
    return output
