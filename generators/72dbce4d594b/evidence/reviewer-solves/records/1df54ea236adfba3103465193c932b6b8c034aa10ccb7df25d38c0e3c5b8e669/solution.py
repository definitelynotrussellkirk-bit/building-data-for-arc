"""Fresh Python solution; command table fitted from the five visible examples."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not isinstance(grid,list) or not grid or not isinstance(grid[0],list) or not grid[0]:
        raise ValueError('expected a nonempty grid')
    height,width=len(grid),len(grid[0])
    if any(not isinstance(row,list) or len(row)!=width for row in grid):
        raise ValueError('expected a rectangular grid')
    if any(type(v) is not int or v not in (0,1,2,3,8) for row in grid for v in row):
        raise ValueError('unexpected cell value')
    remaining={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==1}
    components=[]
    while remaining:
        first=min(remaining)
        remaining.remove(first)
        stack=[first]
        cells=[]
        while stack:
            r,c=stack.pop()
            cells.append((r,c))
            for point in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if point in remaining:
                    remaining.remove(point)
                    stack.append(point)
        components.append(cells)
    components.sort(key=len)
    rank=sum(v==2 for row in grid for v in row)
    code=sum(v==3 for row in grid for v in row)
    targets=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==8]
    if len(components)!=3 or len({len(c) for c in components})!=3:
        raise ValueError('expected three differently sized components')
    if not 1<=rank<=3 or not 1<=code<=4 or len(targets)!=1:
        raise ValueError('invalid instruction counts or target')
    shape=components[rank-1]
    if code==2:
        shape=[(c,-r) for r,c in shape]
    elif code==3:
        shape=[(-r,-c) for r,c in shape]
    elif code==4:
        shape=[(r,-c) for r,c in shape]
    top=min(r for r,c in shape)
    left=min(c for r,c in shape)
    tr,tc=targets[0]
    out=[[0]*width for _ in range(height)]
    for r,c in shape:
        rr,cc=tr+r-top,tc+c-left
        if not (0<=rr<height and 0<=cc<width):
            raise ValueError('transformed shape does not fit')
        out[rr][cc]=7
    return out
