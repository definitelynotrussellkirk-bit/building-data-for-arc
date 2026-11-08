"""Audit rival: select correctly, then erase every non-component crop cell."""
def rival(grid):
    h,w=len(grid),len(grid[0])
    by={};seen=set()
    for r in range(h):
        for c in range(w):
            color=grid[r][c]
            if not color or (r,c) in seen: continue
            todo=[(r,c)];seen.add((r,c));cells=[]
            while todo:
                a,b=todo.pop();cells.append((a,b))
                for nr,nc in ((a-1,b),(a+1,b),(a,b-1),(a,b+1)):
                    if 0<=nr<h and 0<=nc<w and (nr,nc) not in seen and grid[nr][nc]==color:
                        seen.add((nr,nc));todo.append((nr,nc))
            by.setdefault(color,[]).append(cells)
    for color,components in by.items():
        big=[component for component in components if len(component)>1]
        if sum(len(component)==1 for component in components)==1 and len(big)==1:
            cells=big[0]
            r0=min(r for r,c in cells);r1=max(r for r,c in cells)
            c0=min(c for r,c in cells);c1=max(c for r,c in cells)
            result=[[0]*(c1-c0+1) for _ in range(r1-r0+1)]
            for r,c in cells: result[r-r0][c-c0]=color
            return result
    return [[0]]
