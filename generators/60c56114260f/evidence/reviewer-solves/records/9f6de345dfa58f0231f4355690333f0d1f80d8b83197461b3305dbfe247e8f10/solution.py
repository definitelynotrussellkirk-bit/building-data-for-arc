"""Construct an ordered shape-equivalence matrix under rotation/reflection."""
def solve(grid):
    if not grid or not grid[0] or any(len(row)!=len(grid[0]) for row in grid):
        raise ValueError('Expected a nonempty rectangular grid')
    by_color={}
    for r,row in enumerate(grid):
        for c,color in enumerate(row):
            if color != 0:
                by_color.setdefault(color,[]).append((r,c))
    keys=[]
    for cells in by_color.values():
        shapes=[]
        for reflected in (False,True):
            current=[(r,-c if reflected else c) for r,c in cells]
            for _ in range(4):
                r0=min(r for r,c in current); c0=min(c for r,c in current)
                shapes.append(tuple(sorted((r-r0,c-c0) for r,c in current)))
                current=[(c,-r) for r,c in current]
        keys.append(min(shapes))
    return [[8 if a==b else 0 for b in keys] for a in keys]
