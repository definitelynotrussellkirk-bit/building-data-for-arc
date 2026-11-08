def solve(grid):
    objects=[]
    for color in {x for row in grid for x in row if x}:
        cells=[(r,c) for r,row in enumerate(grid) for c,x in enumerate(row) if x==color]
        objects.append((min(cells),max(c for r,c in cells)-min(c for r,c in cells)+1))
    objects.sort()
    widths=[w for _,w in objects]
    return [[1 if a==b else 2 if a>b else 3 for b in widths] for a in widths]
