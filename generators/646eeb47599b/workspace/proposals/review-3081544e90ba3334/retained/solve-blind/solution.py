"""Visible-only solution for the assigned ARC episode."""
from __future__ import annotations

def solve(grid: list[list[int]]) -> list[list[int]]:
    if not grid:
        return []
    h,w=len(grid),len(grid[0])
    out=[row[:] for row in grid]
    seen:set[tuple[int,int]]=set()
    for sr in range(h):
        for sc in range(w):
            color=grid[sr][sc]
            if color==0 or (sr,sc) in seen:
                continue
            comp=[]; stack=[(sr,sc)]; seen.add((sr,sc))
            while stack:
                r,c=stack.pop(); comp.append((r,c))
                for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                    rr,cc=r+dr,c+dc
                    if 0<=rr<h and 0<=cc<w and (rr,cc) not in seen and grid[rr][cc]==color:
                        seen.add((rr,cc)); stack.append((rr,cc))
            rows={r for r,_ in comp}; cols={c for _,c in comp}
            targets=[]
            if len(rows)==1 and len(comp)>=2:
                r=next(iter(rows)); lo=min(c for _,c in comp); hi=max(c for _,c in comp)
                targets=[(r,lo-1),(r,hi+1)]
            elif len(cols)==1 and len(comp)>=2:
                c=next(iter(cols)); lo=min(r for r,_ in comp); hi=max(r for r,_ in comp)
                targets=[(lo-1,c),(hi+1,c)]
            for r,c in targets:
                if 0<=r<h and 0<=c<w and out[r][c] in (0,color):
                    out[r][c]=color
    return out
