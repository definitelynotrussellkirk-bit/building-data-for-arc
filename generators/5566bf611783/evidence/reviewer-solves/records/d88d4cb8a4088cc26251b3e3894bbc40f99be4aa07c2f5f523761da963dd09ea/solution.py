"""Visible-example solution for 5566bf611783."""


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]
    seen = set()

    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] == 5 or (start_r, start_c) in seen:
                continue

            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            chamber = []
            while stack:
                row, col = stack.pop()
                chamber.append((row, col))
                for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = row + drow
                    next_col = col + dcol
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if grid[next_row][next_col] == 5:
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))

            red = sum(grid[row][col] == 2 for row, col in chamber)
            green = sum(grid[row][col] == 3 for row, col in chamber)
            fill = 2 if red > green else 3 if green > red else 8
            for row, col in chamber:
                if grid[row][col] == 0:
                    output[row][col] = fill

    return output
