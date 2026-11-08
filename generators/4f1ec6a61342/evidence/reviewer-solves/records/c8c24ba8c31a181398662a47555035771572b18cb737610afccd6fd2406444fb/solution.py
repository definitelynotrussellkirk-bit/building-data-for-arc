def solve(grid):
    """Select wall-bounded regions by the visible corner's red-cell count."""
    h, w = len(grid), len(grid[0])
    target = grid[0][0]
    output = [[5 if cell == 5 else 0 for cell in row] for row in grid]
    seen = set()
    for row in range(h):
        for col in range(w):
            if grid[row][col] == 5 or (row, col) in seen:
                continue
            cells = [(row, col)]
            seen.add((row, col))
            for r, c in cells:
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < h and 0 <= nc < w
                            and grid[nr][nc] != 5 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        cells.append((nr, nc))
            if sum(grid[r][c] == 2 for r, c in cells) == target:
                for r, c in cells:
                    output[r][c] = 8
    return output
