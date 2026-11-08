def solve(grid):
    """Fill enclosed non-blue regions containing a red marker with yellow."""
    result = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 1 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            region = []
            touches_edge = False
            marked = False
            while stack:
                r, c = stack.pop()
                region.append((r, c))
                touches_edge |= r in (0, height - 1) or c in (0, width - 1)
                marked |= grid[r][c] == 2
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and grid[nr][nc] != 1 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            if marked and not touches_edge:
                for r, c in region:
                    result[r][c] = 4
    return result
