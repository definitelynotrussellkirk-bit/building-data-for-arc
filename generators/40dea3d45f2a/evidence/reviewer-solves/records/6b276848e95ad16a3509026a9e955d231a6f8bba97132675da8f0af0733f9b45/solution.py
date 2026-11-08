"""Infer the pairwise shape relation of the four visible panels."""
def solve(grid):
    if len(grid)!=9 or any(len(row)!=9 for row in grid):
        raise ValueError('expected the 9 by 9 four-panel layout')
    representatives=[]
    for top,left in ((0,0),(0,5),(5,0),(5,5)):
        points=[(r,c) for r in range(4) for c in range(4) if grid[top+r][left+c]!=0]
        if not points:
            representatives.append(())
            continue
        alternatives=[]
        for mirror in (-1,1):
            shape=[(r,mirror*c) for r,c in points]
            for rotation in range(4):
                minrow=min(r for r,c in shape)
                mincol=min(c for r,c in shape)
                alternatives.append(tuple(sorted((r-minrow,c-mincol) for r,c in shape)))
                shape=[(-c,r) for r,c in shape]
        representatives.append(min(alternatives))
    return [[8 if a==b else 0 for b in representatives] for a in representatives]
