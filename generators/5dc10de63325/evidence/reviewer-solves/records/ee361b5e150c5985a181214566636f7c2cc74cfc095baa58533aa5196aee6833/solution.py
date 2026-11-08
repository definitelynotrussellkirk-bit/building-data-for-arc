def solve(grid):
    """Encode complete groups of four azure cells as a repeated 2x2 tile."""
    azure_count = sum(cell == 8 for row in grid for cell in row)
    filled = min(4, azure_count // 4)

    tile = [[0, 0], [0, 0]]
    fill_order = [(1, 1), (1, 0), (0, 1), (0, 0)]
    for row, col in fill_order[:filled]:
        tile[row][col] = 8

    output = [[0] * 5 for _ in range(5)]
    for row_offset in (0, 3):
        for col_offset in (0, 3):
            for row in range(2):
                for col in range(2):
                    output[row_offset + row][col_offset + col] = tile[row][col]
    return output
