def solve(grid):
    """Return the exact crop of the smallest monochrome 4-connected object."""
    height, width = len(grid), len(grid[0])
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
                for delta_row, delta_col in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
            top = min(r for r, _ in cells)
            left = min(c for _, c in cells)
            bottom = max(r for r, _ in cells)
            right = max(c for _, c in cells)
            components.append((len(cells), top, left, bottom, right, color, cells))

    _, top, left, bottom, right, color, cells = min(
        components, key=lambda item: (item[0], item[1], item[2])
    )
    output = [[0] * (right - left + 1) for _ in range(bottom - top + 1)]
    for row, col in cells:
        output[row - top][col - left] = color
    return output
