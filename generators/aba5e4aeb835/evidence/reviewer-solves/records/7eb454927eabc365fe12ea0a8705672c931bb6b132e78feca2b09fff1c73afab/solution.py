def solve(grid):
    """Trace the visible laser from its border marker, preserving all objects."""
    result = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    sources = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == 2]
    if not sources:
        return result
    row, col = sources[0]
    # Compass order: north, east, south, west.
    offsets = ((-1, 0), (0, 1), (1, 0), (0, -1))
    reflection = {3: (1, 0, 3, 2), 4: (3, 2, 1, 0)}
    direction = 1 if col == 0 else 3 if col == width - 1 else 2 if row == 0 else 0
    visited = set()
    while True:
        dr, dc = offsets[direction]
        row += dr
        col += dc
        if not (0 <= row < height and 0 <= col < width):
            break
        color = grid[row][col]
        if color == 5 or (row, col, direction) in visited:
            break
        visited.add((row, col, direction))
        if color == 0:
            result[row][col] = 8
        elif color in reflection:
            direction = reflection[color][direction]
        elif color != 2:
            break
    return result
