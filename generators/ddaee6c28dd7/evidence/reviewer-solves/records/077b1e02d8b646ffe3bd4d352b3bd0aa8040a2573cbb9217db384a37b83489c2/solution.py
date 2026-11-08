def solve(grid):
    """Extract the widest non-background object and recolor it orange (8)."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    objects = []

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
                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and (next_row, next_col) not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add((next_row, next_col))
                        stack.append((next_row, next_col))

            min_row = min(r for r, _ in cells)
            max_row = max(r for r, _ in cells)
            min_col = min(c for _, c in cells)
            max_col = max(c for _, c in cells)
            objects.append((max_col - min_col + 1, len(cells), min_row, max_row, min_col, max_col, set(cells)))

    _, _, min_row, max_row, min_col, max_col, cells = max(objects, key=lambda item: (item[0], item[1]))
    return [
        [8 if (row, col) in cells else 0 for col in range(min_col, max_col + 1)]
        for row in range(min_row, max_row + 1)
    ]
