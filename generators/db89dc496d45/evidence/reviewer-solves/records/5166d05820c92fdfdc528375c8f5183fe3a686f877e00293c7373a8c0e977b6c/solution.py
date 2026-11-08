"""Visible-example solve for ARC task db89dc496d45."""


def solve(grid):
    """Crop the largest 4-connected non-background monochrome object."""
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    seen = set()
    largest = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            component = []
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                current_row, current_col = stack.pop()
                component.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
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

            if len(component) > len(largest):
                largest = component

    if not largest:
        return []

    min_row = min(row for row, _ in largest)
    max_row = max(row for row, _ in largest)
    min_col = min(col for _, col in largest)
    max_col = max(col for _, col in largest)
    selected = set(largest)

    return [
        [
            grid[row][col] if (row, col) in selected else 0
            for col in range(min_col, max_col + 1)
        ]
        for row in range(min_row, max_row + 1)
    ]
