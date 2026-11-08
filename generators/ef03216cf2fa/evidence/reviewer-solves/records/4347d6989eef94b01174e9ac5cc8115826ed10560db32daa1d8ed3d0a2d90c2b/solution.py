def solve(grid):
    """Crop, orient, and vertically arrange the monochrome objects."""
    colors = {color for row in grid for color in row if color != 0}
    if not colors:
        return [list(row) for row in grid]
    objects = []
    for color in sorted(colors):
        points = [(r, c) for r, row in enumerate(grid)
                  for c, value in enumerate(row) if value == color]
        top = min(r for r, c in points)
        bottom = max(r for r, c in points)
        left = min(c for r, c in points)
        right = max(c for r, c in points)
        shape = [[color if grid[r][c] == color else 0
                  for c in range(left, right + 1)]
                 for r in range(top, bottom + 1)]
        if len(shape) > len(shape[0]):
            shape = [list(row) for row in zip(*shape[::-1])]
        objects.append((shape, len(points), top, left))
    objects.sort(key=lambda obj: (-len(obj[0][0]), -obj[1], obj[2], obj[3]))
    width = max(len(obj[0][0]) for obj in objects)
    output = []
    for i, (shape, count, top, left) in enumerate(objects):
        if i:
            output.append([0] * width)
        output.extend(row + [0] * (width - len(row)) for row in shape)
    return output
