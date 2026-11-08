"""Independent Python label claims and explicit finite rival policies."""
from collections import Counter

SCOPES=('all','rarest_tip')
RIVALS=('all','rarest_tip','commonest_tip','first_tip','last_tip','numeric_min','numeric_max',
        'corners','cardinals','pixel_frequency','identity','omit_core','unreflected','rotate_all')
DIRECTIONS=[(i,j) for i in range(3) for j in range(3) if (i,j)!=(1,1)]


def checked_grid(grid):
    if (type(grid) is not list or not 1<=len(grid)<=30 or
        any(type(row) is not list or len(row)!=len(grid[0]) for row in grid) or
        not 1<=len(grid[0])<=30 or
        any(type(v) is not int or not 0<=v<=9 for row in grid for v in row)):
        raise ValueError('rectangular exact-integer 0..9 grid required')
    return grid


def mode(values):
    counts=Counter(values)
    return min(counts,key=lambda c:(-counts[c],c))


def extract(grid):
    checked_grid(grid);bg=mode(v for row in grid for v in row)
    remaining={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v!=bg}
    records=[]
    while remaining:
        start=min(remaining);remaining.remove(start);cells={start};stack=[start]
        while stack:
            r,c=stack.pop()
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    p=r+dr,c+dc
                    if p in remaining:remaining.remove(p);cells.add(p);stack.append(p)
        top=min(r for r,c in cells);left=min(c for r,c in cells)
        expected={(top+r,left+c) for r in range(9) for c in range(9) if not(3<=r<=5 and 3<=c<=5)}
        if cells!=expected:raise ValueError('expected hollow 9x9 foreground ring with 3x3 hole')
        tiles=[]
        for i,j in DIRECTIONS:
            tr=2 if i==0 else 0 if i==2 else 1
            tc=2 if j==0 else 0 if j==2 else 1
            pixels=[row[left+3*j:left+3*j+3] for row in grid[top+3*i:top+3*i+3]]
            tiles.append({'direction':(i,j),'pixels':pixels,'tip':pixels[tr][tc]})
        records.append({'top':top,'left':left,'base':mode(grid[r][c] for r,c in cells),
                        'tiles':tiles,'pixel_counts':Counter(grid[r][c] for r,c in cells),
                        'tip_counts':Counter(t['tip'] for t in tiles)})
    if not records:raise ValueError('no rings')
    return bg,records


def solve(grid,scope='all',rival=None):
    if scope not in SCOPES:raise ValueError('unknown extension_scope')
    policy=rival or scope
    if policy not in RIVALS:raise ValueError('unknown rival')
    _,records=extract(grid);out=[row[:] for row in grid];h=len(grid);w=len(grid[0])
    if policy=='identity':return out
    for rec in records:
        top,left=rec['top'],rec['left'];counts=rec['tip_counts'];tiles=rec['tiles']
        if policy!='omit_core':
            for i in range(3):
                for j in range(3):out[top+3+i][left+3+j]=rec['base']
            for t in tiles:
                i,j=t['direction'];out[top+3+i][left+3+j]=t['tip']
        def selected(t):
            tip=t['tip'];i,j=t['direction']
            if policy in ('all','omit_core','unreflected','rotate_all'):return True
            if policy=='rarest_tip':return counts[tip]==min(counts.values())
            if policy=='commonest_tip':return counts[tip]==max(counts.values())
            if policy=='first_tip':return tip==tiles[0]['tip']
            if policy=='last_tip':return tip==tiles[-1]['tip']
            if policy=='numeric_min':return tip==min(counts)
            if policy=='numeric_max':return tip==max(counts)
            if policy=='corners':return i!=1 and j!=1
            if policy=='cardinals':return i==1 or j==1
            if policy=='pixel_frequency':return rec['pixel_counts'][tip]==min(rec['pixel_counts'][c] for c in counts)
            raise AssertionError(policy)
        for t in tiles:
            if not selected(t):continue
            i,j=t['direction'];pixels=t['pixels']
            for r in range(3):
                for c in range(3):
                    rr=top+6*i-3+r;cc=left+6*j-3+c
                    sr=2-r if i!=1 else r;sc=2-c if j!=1 else c
                    if policy=='unreflected':sr,sc=r,c
                    if policy=='rotate_all':sr,sc=2-r,2-c
                    if 0<=rr<h and 0<=cc<w:out[rr][cc]=pixels[sr][sc]
    return out
