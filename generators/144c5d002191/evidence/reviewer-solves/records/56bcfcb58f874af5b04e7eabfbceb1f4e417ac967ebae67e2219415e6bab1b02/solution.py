"""Visible-example solution authored during the exposed post-repair episode."""


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    if not height or not width:
        return []
    seen = set()
    objects = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row,col) in seen:
                continue
            seen.add((row,col))
            stack = [(row,col)]
            cells = []
            while stack:
                r,c = stack.pop()
                cells.append((r,c))
                for rr,cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                    if (0 <= rr < height and 0 <= cc < width
                            and (rr,cc) not in seen and grid[rr][cc] == color):
                        seen.add((rr,cc))
                        stack.append((rr,cc))
            objects.append((color,sorted(cells)))
    templates = [(color,cells) for color,cells in objects if len(cells) > 1]
    if not templates:
        raise ValueError("No multi-cell template in the observed task domain")
    _, template = max(templates,key=lambda item:len(item[1]))
    top = min(r for r,c in template)
    left = min(c for r,c in template)
    shape = [(r-top,c-left) for r,c in template]
    result = [[0 for _ in range(width)] for _ in range(height)]
    for color,cells in objects:
        if len(cells) != 1:
            continue
        r,c = cells[0]
        for dr,dc in shape:
            rr,cc = r+dr,c+dc
            if 0 <= rr < height and 0 <= cc < width:
                result[rr][cc] = color
    return result
