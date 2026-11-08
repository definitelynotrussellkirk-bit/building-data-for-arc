"""Infer the crop from visible examples only."""

def solve(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    candidates = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            component = []
            while stack:
                r, c = stack.pop()
                component.append((r, c))
                for nr, nc in ((r-1,c), (r+1,c), (r,c-1), (r,c+1)):
                    if 0 <= nr < height and 0 <= nc < width and (nr,nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr,nc))
                        stack.append((nr,nc))
            top = min(r for r,c in component)
            bottom = max(r for r,c in component)
            left = min(c for r,c in component)
            right = max(c for r,c in component)
            if bottom-top+1 == 3 and right-left+1 == 5:
                candidates.append((top,bottom,left,right))
    if len(candidates) != 1:
        raise ValueError('Expected one monochrome object with a 3 by 5 bounding box')
    top,bottom,left,right = candidates[0]
    return [list(row[left:right+1]) for row in grid[top:bottom+1]]
