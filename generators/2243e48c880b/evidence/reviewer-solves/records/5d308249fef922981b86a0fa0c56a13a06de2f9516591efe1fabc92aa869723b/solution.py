"""Visible-example solution for task 2243e48c880b."""


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []

    # Row-major discovery is retained as the stable tie-break for equal sizes.
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = [(row, col)]
            seen.add((row, col))
            cells = []
            while queue:
                current_row, current_col = queue.pop(0)
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
                    queue.append((next_row, next_col))
            components.append(cells)

    ranked = sorted(components, key=len)  # Python sort is stable.
    output = [[0 for _ in range(width)] for _ in range(height)]
    for replacement, cells in zip((2, 4, 8), ranked):
        for row, col in cells:
            output[row][col] = replacement
    return output
