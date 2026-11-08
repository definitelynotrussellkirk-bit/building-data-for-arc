from collections import Counter


def solve(grid):
    """Recolor every repeated 8-connected nonzero shape from 5 to 1."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    objects = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for delta_row in (-1, 0, 1):
                    for delta_col in (-1, 0, 1):
                        if delta_row == 0 and delta_col == 0:
                            continue
                        next_row = current_row + delta_row
                        next_col = current_col + delta_col
                        if not (0 <= next_row < height and 0 <= next_col < width):
                            continue
                        if grid[next_row][next_col] == 0:
                            continue
                        if (next_row, next_col) in seen:
                            continue
                        seen.add((next_row, next_col))
                        stack.append((next_row, next_col))

            min_row = min(cell_row for cell_row, _ in cells)
            min_col = min(cell_col for _, cell_col in cells)
            signature = tuple(sorted(
                (cell_row - min_row, cell_col - min_col)
                for cell_row, cell_col in cells
            ))
            objects.append((cells, signature))

    signature_counts = Counter(signature for _, signature in objects)
    output = [row[:] for row in grid]
    for cells, signature in objects:
        if signature_counts[signature] > 1:
            for row, col in cells:
                output[row][col] = 1
    return output
