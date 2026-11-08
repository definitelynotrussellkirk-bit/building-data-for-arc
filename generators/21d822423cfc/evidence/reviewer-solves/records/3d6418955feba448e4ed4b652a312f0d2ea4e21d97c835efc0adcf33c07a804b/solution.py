def solve(grid):
    """Fill a wall-bounded chamber when it contains exactly one colored seed."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] == 5 or (start_row, start_col) in seen:
                continue

            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            chamber = []
            seeds = []

            while stack:
                row, col = stack.pop()
                chamber.append((row, col))
                if grid[row][col] not in (0, 5):
                    seeds.append(grid[row][col])

                for next_row, next_col in (
                    (row - 1, col),
                    (row + 1, col),
                    (row, col - 1),
                    (row, col + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if grid[next_row][next_col] == 5:
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))

            if len(seeds) == 1:
                fill_color = seeds[0]
                for row, col in chamber:
                    out[row][col] = fill_color

    return out
