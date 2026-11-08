def solve(grid):
    """Expand cells with no nonzero cardinal neighbor, preserving connected cells."""
    if not isinstance(grid, (list, tuple)) or not grid or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("expected integer colors 0 through 9")
    height = len(grid)
    output = [list(row) for row in grid]
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue
            neighbors = [(row+dr, col+dc) for dr, dc in directions
                         if 0 <= row+dr < height and 0 <= col+dc < width]
            if any(grid[r][c] != 0 for r, c in neighbors):
                continue
            for r, c in neighbors:
                if output[r][c] == 0:
                    output[r][c] = color
    return output
