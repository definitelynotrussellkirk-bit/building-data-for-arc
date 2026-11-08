def solve(grid):
    """Decode the two-row palette key, then recolor the remaining rows."""
    source_colors = [color for color in grid[0] if color != 0]
    target_colors = [color for color in grid[1] if color != 0]
    color_map = dict(zip(source_colors, target_colors))

    return [
        [color_map.get(color, color) for color in row]
        for row in grid[2:]
    ]
