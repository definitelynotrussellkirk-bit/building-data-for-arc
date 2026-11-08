def solve(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    blocks = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                for a, b in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if 0 <= a < h and 0 <= b < w and (a,b) not in seen and grid[a][b] == color:
                        seen.add((a,b))
                        stack.append((a,b))
            r0, r1 = min(x for x,y in cells), max(x for x,y in cells)
            c0, c1 = min(y for x,y in cells), max(y for x,y in cells)
            if r1 > r0 and c1 > c0 and len(cells) == (r1-r0+1)*(c1-c0+1):
                blocks.append(((r0+r1)//2, (c0+c1)//2, color))
    claims = [[set() for _ in range(w)] for _ in range(h)]
    for r, c, color in blocks:
        for y in range(w):
            claims[r][y].add(color)
        for x in range(h):
            claims[x][c].add(color)
    out = [list(row) for row in grid]
    for r in range(h):
        for c in range(w):
            if claims[r][c]:
                out[r][c] = next(iter(claims[r][c])) if len(claims[r][c]) == 1 else 0
    return out
