def solve(grid):
    height, width = len(grid), len(grid[0])
    erase = set()
    for r in range(height):
        for c in range(width):
            if grid[r][c] != 0:
                continue
            color = None
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] != 0:
                    color = grid[nr][nc]
                    break
            if color is None:
                continue
            along_row = sum(value in (0, color) for value in grid[r])
            along_column = sum(grid[nr][c] in (0, color) for nr in range(height))
            if along_row >= along_column:
                erase.update((nr, c) for nr in range(height) if grid[nr][c] == color)
            else:
                erase.update((r, nc) for nc in range(width) if grid[r][nc] == color)
    return [[0 if (r, c) in erase else value for c, value in enumerate(row)]
            for r, row in enumerate(grid)]
