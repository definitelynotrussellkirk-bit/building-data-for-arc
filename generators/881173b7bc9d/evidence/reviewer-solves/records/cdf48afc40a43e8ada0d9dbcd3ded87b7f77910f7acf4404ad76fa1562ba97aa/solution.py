def solve(grid):
    """Find complete colored outlines and concatenate their full interiors."""
    height, width = len(grid), len(grid[0])
    seen = set()
    pieces = []
    for y in range(height):
        for x in range(width):
            if grid[y][x] == 0 or (y, x) in seen:
                continue
            value = grid[y][x]
            todo = [(y, x)]
            region = set()
            seen.add((y, x))
            while todo:
                a, b = todo.pop()
                region.add((a, b))
                for c, d in ((a - 1, b), (a + 1, b), (a, b - 1), (a, b + 1)):
                    if (0 <= c < height and 0 <= d < width and
                            (c, d) not in seen and grid[c][d] == value):
                        seen.add((c, d))
                        todo.append((c, d))
            top, bottom = min(a for a, b in region), max(a for a, b in region)
            left, right = min(b for a, b in region), max(b for a, b in region)
            if bottom - top < 2 or right - left < 2:
                continue
            outline = {(a, b) for a in range(top, bottom + 1)
                       for b in range(left, right + 1)
                       if a in (top, bottom) or b in (left, right)}
            if region == outline:
                pieces.append((left, [row[left + 1:right]
                                      for row in grid[top + 1:bottom]]))
    if not pieces:
        return [[0]]
    pieces.sort(key=lambda item: item[0])
    out_height = max(len(part) for left, part in pieces)
    output = [[] for _ in range(out_height)]
    for index, (left, part) in enumerate(pieces):
        for row_index in range(out_height):
            if index:
                output[row_index].append(0)
            output[row_index].extend(part[row_index] if row_index < len(part)
                                     else [0] * len(part[0]))
    return output
