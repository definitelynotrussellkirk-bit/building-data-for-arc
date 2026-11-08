def solve(grid):
    """Count cyan, form a two-by-two glyph, and repeat it four times."""
    count = sum(cell == 8 for row in grid for cell in row)
    filled = count // 4
    tile = [[0, 0], [0, 0]]
    for row, col in [(1, 1), (1, 0), (0, 1), (0, 0)][:filled]:
        tile[row][col] = 8
    output = [[0] * 5 for _ in range(5)]
    for row_offset in (0, 3):
        for col_offset in (0, 3):
            for row in range(2):
                for col in range(2):
                    output[row_offset + row][col_offset + col] = tile[row][col]
    return output
