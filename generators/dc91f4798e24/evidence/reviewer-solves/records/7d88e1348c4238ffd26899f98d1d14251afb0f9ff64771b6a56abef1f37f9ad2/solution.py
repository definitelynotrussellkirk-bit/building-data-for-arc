def solve(grid):
    """Summarize the number of 4-connected components of colors 1, 2, and 3."""
    height = len(grid)
    width = len(grid[0]) if height else 0

    def component_count(color):
        seen = set()
        count = 0
        for row in range(height):
            for col in range(width):
                if grid[row][col] != color or (row, col) in seen:
                    continue
                count += 1
                stack = [(row, col)]
                seen.add((row, col))
                while stack:
                    current_row, current_col = stack.pop()
                    for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        neighbor_row = current_row + delta_row
                        neighbor_col = current_col + delta_col
                        if not (0 <= neighbor_row < height and 0 <= neighbor_col < width):
                            continue
                        neighbor = (neighbor_row, neighbor_col)
                        if neighbor in seen or grid[neighbor_row][neighbor_col] != color:
                            continue
                        seen.add(neighbor)
                        stack.append(neighbor)
        return count

    counts = [component_count(color) for color in (1, 2, 3)]
    output_width = max(counts)
    return [
        [color] * count + [0] * (output_width - count)
        for color, count in zip((1, 2, 3), counts)
    ]
