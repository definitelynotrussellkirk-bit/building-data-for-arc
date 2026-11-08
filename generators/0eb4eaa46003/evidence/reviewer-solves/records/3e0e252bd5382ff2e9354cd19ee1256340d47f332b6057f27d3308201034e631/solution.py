"""Visible-example solution: two colored profiles select a connected crop."""

def solve(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for nr, nc in ((r-1,c), (r+1,c), (r,c-1), (r,c+1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr,nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr,nc))
                        stack.append((nr,nc))
            top = min(r for r,c in cells)
            left = min(c for r,c in cells)
            bottom = max(r for r,c in cells)
            right = max(c for r,c in cells)
            rows = tuple(sum(r == i for r,c in cells) for i in range(top,bottom+1))
            cols = tuple(sum(c == j for r,c in cells) for j in range(left,right+1))
            components.append((top,left,color,cells,rows,cols))
    components.sort(key=lambda item: item[:2])
    blue = next(item for item in components if item[2] == 1)
    red = next(item for item in components if item[2] == 2)
    selected = next(item for item in components
                    if item[2] not in (1,2) and item[4] == blue[4] and item[5] == red[5])
    top,left,_,cells,rows,cols = selected
    output = [[0] * len(cols) for _ in rows]
    for r,c in cells:
        output[r-top][c-left] = 8
    return output
