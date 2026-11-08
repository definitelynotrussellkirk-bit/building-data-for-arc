from collections import Counter


def solve(grid):
    """Extract the small palette and mask it with the large block pattern."""
    height = len(grid)
    width = len(grid[0])

    counts = Counter(value for row in grid for value in row if value != 0)
    shape_color = max(counts, key=counts.get)

    # Every non-shape nonzero cell belongs to the dense small palette.  Its
    # bounding box also contains any palette entry equal to shape_color.
    palette_support = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, shape_color)
    ]
    pr0 = min(row for row, _ in palette_support)
    pr1 = max(row for row, _ in palette_support)
    pc0 = min(col for _, col in palette_support)
    pc1 = max(col for _, col in palette_support)
    side = pr1 - pr0 + 1
    palette = [row[pc0 : pc1 + 1] for row in grid[pr0 : pr1 + 1]]

    # Remove the palette box before locating the large shape, because one
    # palette cell can reuse the shape color.
    shape_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == shape_color
        and not (pr0 <= row <= pr1 and pc0 <= col <= pc1)
    ]
    sr0 = min(row for row, _ in shape_cells)
    sr1 = max(row for row, _ in shape_cells)
    sc0 = min(col for _, col in shape_cells)
    sc1 = max(col for _, col in shape_cells)
    block_h = (sr1 - sr0 + 1) // side
    block_w = (sc1 - sc0 + 1) // side

    output = []
    for block_row in range(side):
        out_row = []
        for block_col in range(side):
            r0 = sr0 + block_row * block_h
            c0 = sc0 + block_col * block_w
            filled = any(
                grid[row][col] == shape_color
                for row in range(r0, r0 + block_h)
                for col in range(c0, c0 + block_w)
            )
            out_row.append(palette[block_row][block_col] if filled else 0)
        output.append(out_row)
    return output
