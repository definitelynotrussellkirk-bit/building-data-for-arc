def solve(grid):
    """Overlay the four equal quadrants in their inferred precedence order."""
    height = len(grid) // 2
    width = len(grid[0]) // 2
    result = []
    for row in range(height):
        output_row = []
        for col in range(width):
            candidates = (
                grid[row][col + width],
                grid[row + height][col],
                grid[row + height][col + width],
                grid[row][col],
            )
            output_row.append(next((color for color in candidates if color != 0), 0))
        result.append(output_row)
    return result
