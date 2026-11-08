def solve(grid):
    """Encode complete groups of four azure cells in four mirrored 2x2 counters."""
    azure_count = sum(cell == 8 for row in grid for cell in row)
    complete_groups = min(4, azure_count // 4)

    # The 2x2 counter fills from the lower-right, leftward, then upward.
    fill_order = ((1, 1), (1, 0), (0, 1), (0, 0))
    motif = [[0, 0], [0, 0]]
    for row, col in fill_order[:complete_groups]:
        motif[row][col] = 8

    output = [[0] * 5 for _ in range(5)]
    for row_offset, col_offset in ((0, 0), (0, 3), (3, 0), (3, 3)):
        for row in range(2):
            for col in range(2):
                output[row_offset + row][col_offset + col] = motif[row][col]
    return output
