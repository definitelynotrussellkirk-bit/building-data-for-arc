def solve(grid):
    """Recolor each non-corner object by the closest corner marker."""
    height, width = len(grid), len(grid[0])
    corners = ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1))
    corner_set = set(corners)

    # Build 4-connected components separately for each nonzero color.
    by_color = {}
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color:
                by_color.setdefault(color, set()).add((row, col))

    objects = []
    for color, points in by_color.items():
        remaining = set(points)
        while remaining:
            first = min(remaining)
            remaining.remove(first)
            cells, stack = {first}, [first]
            while stack:
                row, col = stack.pop()
                for point in ((row - 1, col), (row + 1, col),
                              (row, col - 1), (row, col + 1)):
                    if point in remaining:
                        remaining.remove(point)
                        cells.add(point)
                        stack.append(point)
            objects.append((color, cells))

    output = [[0] * width for _ in range(height)]
    for row, col in corners:
        output[row][col] = grid[row][col]

    for _color, cells in objects:
        if len(cells) == 1 and next(iter(cells)) in corner_set:
            continue
        row_min = min(row for row, _ in cells)
        row_max = max(row for row, _ in cells)
        col_min = min(col for _, col in cells)
        col_max = max(col for _, col in cells)

        # Compare doubled bounding-box centers, avoiding fractions.  The
        # visible examples' exact midpoint cases choose top and then left.
        bottom = row_min + row_max > height - 1
        right = col_min + col_max > width - 1
        corner_index = 2 * int(bottom) + int(right)
        target_color = grid[corners[corner_index][0]][corners[corner_index][1]]
        for row, col in cells:
            output[row][col] = target_color
    return output
