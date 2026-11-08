def solve(grid):
    """Rank nonzero objects by size, then reading order, and recolor them."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + dr
                    next_col = current_col + dc
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))

            components.append(cells)

    components.sort(key=lambda cells: (len(cells), min(cells)))
    palette = (2, 4, 6, 8)
    if len(components) != len(palette):
        raise ValueError(f"expected four objects, found {len(components)}")

    output = [row[:] for row in grid]
    for new_color, cells in zip(palette, components):
        for row, col in cells:
            output[row][col] = new_color
    return output
