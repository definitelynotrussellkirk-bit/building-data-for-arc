def solve(grid):
    out=[row[:] for row in grid]
    colors={c for row in grid for c in row if c}
    for c in colors:
        pos=[(r,k) for r,row in enumerate(grid) for k,v in enumerate(row) if v==c]
        for i,(r,k) in enumerate(pos):
            for rr,kk in pos[i+1:]:
                if r==rr:
                    for x in range(min(k,kk),max(k,kk)+1):
                        if out[r][x]==0:out[r][x]=c
                elif k==kk:
                    for y in range(min(r,rr),max(r,rr)+1):
                        if out[y][k]==0:out[y][k]=c
    return out
