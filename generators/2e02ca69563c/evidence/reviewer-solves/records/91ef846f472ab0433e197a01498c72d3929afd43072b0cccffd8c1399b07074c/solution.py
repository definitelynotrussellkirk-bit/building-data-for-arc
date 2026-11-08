"""Connect equal-colored endpoint pairs independently inside each rectangle."""
from collections import defaultdict


def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('Expected a rectangular grid')
    h,w = len(grid),len(grid[0])
    visited = set()
    rectangles = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r,c) in visited:
                continue
            todo = [(r,c)]
            visited.add((r,c))
            component = set()
            while todo:
                rr,cc = todo.pop()
                component.add((rr,cc))
                for nr,nc in ((rr-1,cc),(rr+1,cc),(rr,cc-1),(rr,cc+1)):
                    if (0 <= nr < h and 0 <= nc < w and (nr,nc) not in visited
                        and grid[nr][nc] == color):
                        visited.add((nr,nc))
                        todo.append((nr,nc))
            top = min(rr for rr,cc in component)
            bottom = max(rr for rr,cc in component)
            left = min(cc for rr,cc in component)
            right = max(cc for rr,cc in component)
            if bottom-top < 2 or right-left < 2:
                continue
            perimeter = {(rr,cc) for rr in range(top,bottom+1) for cc in range(left,right+1)
                         if rr in (top,bottom) or cc in (left,right)}
            if perimeter == component:
                rectangles.append((top,left,bottom,right,color))
    result = [list(row) for row in grid]
    for top,left,bottom,right,frame_color in rectangles:
        points = defaultdict(list)
        for r in range(top+1,bottom):
            for c in range(left+1,right):
                if grid[r][c] not in (0,frame_color):
                    points[grid[r][c]].append((r,c))
        for color,pair in points.items():
            if len(pair) != 2:
                continue
            (r0,c0),(r1,c1) = sorted(pair)
            for c in range(min(c0,c1),max(c0,c1)+1):
                result[r0][c] = color
            for r in range(r0,r1+1):
                result[r][c1] = color
    return result
