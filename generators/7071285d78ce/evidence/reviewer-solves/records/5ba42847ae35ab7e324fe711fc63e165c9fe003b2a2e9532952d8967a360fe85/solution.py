def solve(grid):
    """Transpose each monochromatic component about its bounding-box origin."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [[0 for _ in range(width)] for _ in range(height)]
    visited = set()
    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color == 0 or (row, column) in visited:
                continue
            component = []
            pending = [(row, column)]
            visited.add((row, column))
            while pending:
                current_row, current_column = pending.pop()
                component.append((current_row, current_column))
                for next_row, next_column in (
                    (current_row - 1, current_column),
                    (current_row + 1, current_column),
                    (current_row, current_column - 1),
                    (current_row, current_column + 1),
                ):
                    if (0 <= next_row < height and 0 <= next_column < width
                            and (next_row, next_column) not in visited
                            and grid[next_row][next_column] == color):
                        visited.add((next_row, next_column))
                        pending.append((next_row, next_column))
            top = min(cell[0] for cell in component)
            left = min(cell[1] for cell in component)
            for source_row, source_column in component:
                target_row = top + source_column - left
                target_column = left + source_row - top
                result[target_row][target_column] = color
    return result
