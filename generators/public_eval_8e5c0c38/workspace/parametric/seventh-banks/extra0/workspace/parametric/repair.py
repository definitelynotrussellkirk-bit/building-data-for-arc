"""Pure input-dependent symmetry records and selective repair claims.

Protected Racket remains the execution authority. Foreground colors, not connected
components, define silhouettes; maximum reflected support selects a doubled axis,
with the leftmost maximizer on ties. Damage counts unmatched occupied cells.
"""
from collections import Counter
from copy import deepcopy

MODES=('trim','complete','complete_most_damaged')

def analyze(grid):
    if (type(grid) is not list or not 1<=len(grid)<=30 or
        any(type(row) is not list for row in grid) or not 1<=len(grid[0])<=30 or
        any(len(row)!=len(grid[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
        raise ValueError('expected rectangular exact-integer ARC grid, size 1..30')
    counts=Counter(v for row in grid for v in row)
    bg=min(counts,key=lambda c:(-counts[c],c))
    records=[]
    for color in sorted(set(counts)-{bg}):
        cells={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==color}
        lo,hi=min(c for r,c in cells),max(c for r,c in cells)
        scores={k:sum((r,k-c) in cells for r,c in cells) for k in range(2*lo,2*hi+1)}
        axis=min(scores,key=lambda k:(-scores[k],k))
        records.append(dict(color=color,cells=cells,axis2=axis,
                            damage=len(cells)-scores[axis],score=scores[axis],
                            maximizers=[k for k,s in scores.items() if s==scores[axis]]))
    return bg,records

def solve(grid,mode='trim'):
    if type(mode) is not str or mode not in MODES:
        raise ValueError('unknown repair rule')
    bg,records=analyze(grid)
    largest=max((r['damage'] for r in records),default=0)
    out=deepcopy(grid)
    for record in records:
        color,cells,axis=record['color'],record['cells'],record['axis2']
        complete=mode=='complete' or (mode=='complete_most_damaged' and largest>0 and record['damage']==largest)
        for r,c in sorted(cells):
            mirror=(r,axis-c)
            if complete:
                rr,cc=mirror
                if 0<=cc<len(grid[0]) and grid[rr][cc]==bg:out[rr][cc]=color
            elif mirror not in cells:
                out[r][c]=bg
    return out
