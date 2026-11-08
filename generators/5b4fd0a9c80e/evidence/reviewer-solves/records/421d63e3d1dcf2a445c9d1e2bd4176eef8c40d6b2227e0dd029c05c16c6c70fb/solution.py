def solve(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    objects = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            cells = []
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for rr, cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                    if 0 <= rr < height and 0 <= cc < width and (rr,cc) not in seen and grid[rr][cc] == color:
                        seen.add((rr,cc))
                        stack.append((rr,cc))
            top = min(r for r,c in cells)
            left = min(c for r,c in cells)
            h = max(r for r,c in cells) - top + 1
            w = max(c for r,c in cells) - left + 1
            objects.append((len(cells), top, left, h, w, color, cells))
    objects.sort(key=lambda obj: (obj[0], obj[1], obj[2]))
    if not objects:
        return [list(row) for row in grid]
    output_width = max(obj[4] for obj in objects)
    output_height = sum(obj[3] for obj in objects) + len(objects) - 1
    result = [[0] * output_width for _ in range(output_height)]
    cursor = 0
    for area, top, left, h, w, color, cells in objects:
        offset = (output_width - w) // 2
        for r,c in cells:
            result[cursor+r-top][offset+c-left] = color
        cursor += h + 1
    return result
