from collections import Counter


def solve(grid):
    """Crop the rightmost non-singleton monochromatic 4-connected object."""
    height = len(grid)
    width = len(grid[0])
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]

    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == background or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            cells = []

            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
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

            if len(cells) > 1:
                rows = [cell_row for cell_row, _ in cells]
                cols = [cell_col for _, cell_col in cells]
                components.append(
                    (
                        max(cols),
                        len(cells),
                        min(rows),
                        min(cols),
                        max(rows),
                        max(cols),
                    )
                )

    if not components:
        return [row[:] for row in grid]

    _, _, top, left, bottom, right = max(components)
    return [row[left : right + 1] for row in grid[top : bottom + 1]]
