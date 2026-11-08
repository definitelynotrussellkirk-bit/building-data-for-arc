def solve(grid):
    if not grid:
        return []
    column_colors = []
    for column in range(len(grid[0])):
        seeds = [row[column] for row in grid if row[column] != 0]
        column_colors.append(seeds[0] if len(seeds) == 1 else 0)
    return [column_colors[:] for _ in grid]
