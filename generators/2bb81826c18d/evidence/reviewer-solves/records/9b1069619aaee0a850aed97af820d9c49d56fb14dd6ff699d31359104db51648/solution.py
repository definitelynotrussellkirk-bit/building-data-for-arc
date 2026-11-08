"""Infer a bordered checkerboard pattern from the visible rectangle examples."""


def solve(grid):
    result = [list(row) for row in grid]
    if not grid:
        return result
    height, width = len(grid), len(grid[0])
    seen = set()

    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            component = []
            pending = [(start_row, start_col)]
            seen.add((start_row, start_col))
            while pending:
                row, col = pending.pop()
                component.append((row, col))
                for next_row, next_col in ((row - 1, col), (row + 1, col),
                                           (row, col - 1), (row, col + 1)):
                    if (0 <= next_row < height and 0 <= next_col < width
                            and (next_row, next_col) not in seen
                            and grid[next_row][next_col] == color):
                        seen.add((next_row, next_col))
                        pending.append((next_row, next_col))

            top = min(row for row, col in component)
            bottom = max(row for row, col in component)
            left = min(col for row, col in component)
            right = max(col for row, col in component)
            for row, col in component:
                if (top < row < bottom and left < col < right
                        and ((row - top) + (col - left)) % 2 == 0):
                    result[row][col] = 0
    return result
