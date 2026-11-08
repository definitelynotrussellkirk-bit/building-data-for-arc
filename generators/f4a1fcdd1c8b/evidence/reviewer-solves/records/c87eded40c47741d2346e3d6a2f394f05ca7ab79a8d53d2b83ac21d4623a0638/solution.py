def solve(grid):
    """Keep exactly the nonzero 4-connected components touching the border."""
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    if width == 0:
        return [[] for _ in grid]
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    output = [[0] * width for _ in range(height)]
    seen = set()

    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue

            component = []
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            touches_border = False

            while stack:
                row, col = stack.pop()
                component.append((row, col))
                touches_border = touches_border or (
                    row == 0
                    or row == height - 1
                    or col == 0
                    or col == width - 1
                )

                for d_row, d_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = row + d_row
                    next_col = col + d_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))

            if touches_border:
                for row, col in component:
                    output[row][col] = color

    return output
