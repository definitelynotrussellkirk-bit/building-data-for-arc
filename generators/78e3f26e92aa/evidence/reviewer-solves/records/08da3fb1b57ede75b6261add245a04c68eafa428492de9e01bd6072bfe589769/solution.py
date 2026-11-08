def solve(grid):
    """Extend each pair of bars outwards in height-sized stair steps."""
    height = len(grid)
    width = len(grid[0])
    layers = []
    for color in (3, 8):
        cells = [(r, c) for r, row in enumerate(grid)
                 for c, value in enumerate(row) if value == color]
        if not cells:
            continue
        first_row = min(r for r, c in cells)
        last_row = max(r for r, c in cells)
        left = min(c for r, c in cells)
        right = max(c for r, c in cells)
        step_height = last_row - first_row + 1
        layer = set()
        for r in range(height):
            distance = max(first_row - r, r - last_row, 0)
            shift = (distance + step_height - 1) // step_height
            for c in (left - shift, right + shift):
                if 0 <= c < width:
                    layer.add((r, c))
        layers.append((color, layer))
    result = [[0] * width for _ in range(height)]
    for color, layer in layers:
        for r, c in layer:
            result[r][c] = color if result[r][c] == 0 else 6
    return result
