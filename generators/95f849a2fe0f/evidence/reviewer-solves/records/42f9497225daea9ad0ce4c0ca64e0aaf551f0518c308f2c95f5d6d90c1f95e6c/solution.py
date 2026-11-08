def solve(grid):
    colors = sorted({cell for row in grid for cell in row if cell != 0})
    if len(colors) != 2:
        raise ValueError("Expected two foreground objects")
    shapes = []
    for color in colors:
        cells = [(r, c) for r, row in enumerate(grid)
                 for c, value in enumerate(row) if value == color]
        top = min(r for r, c in cells)
        left = min(c for r, c in cells)
        shapes.append({(r - top, c - left) for r, c in cells})
    height = 1 + max(r for shape in shapes for r, c in shape)
    width = 1 + max(c for shape in shapes for r, c in shape)
    difference = shapes[0] ^ shapes[1]
    return [[8 if (r, c) in difference else 0 for c in range(width)]
            for r in range(height)]
