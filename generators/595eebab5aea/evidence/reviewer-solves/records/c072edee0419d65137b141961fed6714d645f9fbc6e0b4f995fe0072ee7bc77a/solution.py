"""Infer the transformation from the visible example grids only."""


def solve(grid):
    """Rank body shapes by size, recolor, and stack their centered crops."""
    rows = [list(row) for row in grid]
    if not rows or not rows[0]:
        raise ValueError("Expected a nonempty grid")
    height, width = len(rows), len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("Expected a rectangular grid")

    # The first row supplies the output colors in left-to-right order.
    palette = [value for value in rows[0] if value != 0]
    unseen = {
        (r, c)
        for r in range(1, height)
        for c in range(width)
        if rows[r][c] != 0
    }
    shapes = []
    while unseen:
        start = min(unseen)
        color = rows[start[0]][start[1]]
        unseen.remove(start)
        stack = [start]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in unseen and rows[neighbor[0]][neighbor[1]] == color:
                    unseen.remove(neighbor)
                    stack.append(neighbor)
        top = min(r for r, c in cells)
        left = min(c for r, c in cells)
        bottom = max(r for r, c in cells)
        right = max(c for r, c in cells)
        shapes.append((cells, top, left, bottom - top + 1, right - left + 1))

    if not shapes or len(shapes) != len(palette):
        raise ValueError("Expected one top-row color marker per body shape")

    # Example 3 places equal-size shapes in row-major positional order.
    shapes.sort(key=lambda shape: (-len(shape[0]), shape[1], shape[2]))
    output_width = max(shape[4] for shape in shapes)
    output_height = sum(shape[3] for shape in shapes) + len(shapes) - 1
    output = [[0] * output_width for _ in range(output_height)]
    output_top = 0
    for color, (cells, top, left, shape_height, shape_width) in zip(palette, shapes):
        output_left = (output_width - shape_width) // 2
        for r, c in cells:
            output[output_top + r - top][output_left + c - left] = color
        output_top += shape_height + 1
    return output
