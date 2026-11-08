"""Recolor same-color connected components by bounding-box containment count."""
def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('Expected a nonempty rectangular grid')
    height, width = len(grid), len(grid[0])
    seen = set()
    parts = []
    for r in range(height):
        for c in range(width):
            if not grid[r][c] or (r,c) in seen:
                continue
            color = grid[r][c]
            stack = [(r,c)]
            seen.add((r,c))
            cells = []
            while stack:
                a,b = stack.pop()
                cells.append((a,b))
                for x,y in ((a-1,b),(a+1,b),(a,b-1),(a,b+1)):
                    if (0 <= x < height and 0 <= y < width and
                        (x,y) not in seen and grid[x][y] == color):
                        seen.add((x,y))
                        stack.append((x,y))
            box = (min(a for a,b in cells), min(b for a,b in cells),
                   max(a for a,b in cells), max(b for a,b in cells))
            parts.append((cells,box))
    result = [[0] * width for _ in range(height)]
    for cells, box in parts:
        containers = sum(parent != box and parent[0] <= box[0] and
                         parent[1] <= box[1] and parent[2] >= box[2] and
                         parent[3] >= box[3] for _,parent in parts)
        color = (2,3,4,5,6)[containers] if containers < 5 else 9
        for r,c in cells:
            result[r][c] = color
    return result
