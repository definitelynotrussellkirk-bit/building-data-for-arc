def solve(grid):
    """Recolor the first smallest non-background component to 9."""
    output = [list(row) for row in grid]
    if not grid or not grid[0]:
        return output
    height, width = len(grid), len(grid[0])
    seen = set()
    objects = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            cells = [(row, col)]
            seen.add((row, col))
            for y, x in cells:
                for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if (0 <= yy < height and 0 <= xx < width
                            and (yy, xx) not in seen and grid[yy][xx] == color):
                        seen.add((yy, xx))
                        cells.append((yy, xx))
            objects.append(cells)
    if objects:
        for row, col in min(objects, key=len):
            output[row][col] = 9
    return output
