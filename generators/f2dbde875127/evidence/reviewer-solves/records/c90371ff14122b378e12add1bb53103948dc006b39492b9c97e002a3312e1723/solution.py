"""An explicit hypothesis family fitted only to the public demonstrations."""
from collections import deque


def compartments(grid):
    """Locate separated blue boundaries by four-neighbor connectivity."""
    height, width = len(grid), len(grid[0])
    seen = set()
    boxes = []
    for r in range(height):
        for c in range(width):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            points = []
            while queue:
                y, x = queue.popleft()
                points.append((y, x))
                for yy, xx in ((y-1, x), (y+1, x), (y, x-1), (y, x+1)):
                    if 0 <= yy < height and 0 <= xx < width and grid[yy][xx] == 1 and (yy, xx) not in seen:
                        seen.add((yy, xx)); queue.append((yy, xx))
            top = min(y for y, x in points)
            bottom = max(y for y, x in points)
            left = min(x for y, x in points)
            right = max(x for y, x in points)
            if top == 0 or bottom-top < 2 or right-left < 2:
                raise ValueError('blue boundary lacks an interior or an overhead marker')
            border = {(y, x) for y in range(top, bottom+1) for x in range(left, right+1)
                      if y in (top, bottom) or x in (left, right)}
            if set(points) != border:
                raise ValueError('blue component is not a rectangular boundary')
            boxes.append((top, left, bottom, right))
    return sorted(boxes)


def apply_hypothesis(grid, slope, intercept, ceil_r=False, ceil_c=False):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('expected a nonempty rectangular grid')
    output = [list(row) for row in grid]
    for top, left, bottom, right in compartments(grid):
        markers = [grid[top-1][x] for x in range(left, right+1) if grid[top-1][x] not in (0, 1)]
        if len(markers) != 1:
            raise ValueError('expected one overhead marker')
        points = [(y, x, grid[y][x]) for y in range(top+1, bottom) for x in range(left+1, right)
                  if grid[y][x] != 0]
        if not points or len({color for y, x, color in points}) != 1:
            raise ValueError('expected a single-color interior piece')
        first_y, first_x = min(y for y, x, v in points), min(x for y, x, v in points)
        cells = [(y-first_y, x-first_x, v) for y, x, v in points]
        for _ in range((slope*markers[0]+intercept) % 4):
            h = max(y for y, x, v in cells)+1
            cells = [(x, h-1-y, v) for y, x, v in cells]
        h, w = max(y for y, x, v in cells)+1, max(x for y, x, v in cells)+1
        gap_y, gap_x = bottom-top-1-h, right-left-1-w
        if gap_y < 0 or gap_x < 0:
            raise ValueError('transformed piece exceeds its compartment')
        dest_y = top+1+(gap_y+int(ceil_r))//2
        dest_x = left+1+(gap_x+int(ceil_c))//2
        for y in range(top+1, bottom):
            for x in range(left+1, right):
                output[y][x] = 0
        for y, x, color in cells:
            output[dest_y+y][dest_x+x] = color
    return output



def solve(grid):
    """Visible-fit affine key hypothesis; masked-query correctness unscored."""
    return apply_hypothesis(grid, slope=1, intercept=2, ceil_r=False, ceil_c=False)
