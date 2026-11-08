"""Keyed jigsaw assembly; all solutions are computed from geometry, never fixtures."""
from __future__ import annotations
from collections import Counter
from math import isqrt

D4=((-1,0),(1,0),(0,-1),(0,1))

def grid(g):
    if type(g) is not list or not 1<=len(g)<=30 or any(type(row)is not list for row in g):
        raise ValueError('Expected a list grid with 1..30 rows')
    w=len(g[0])
    if not 1<=w<=30 or any(len(row)!=w for row in g):raise ValueError('Ragged or oversized grid')
    if any(type(x)is not int or not 0<=x<=9 for row in g for x in row):raise ValueError('Exact integer colors 0..9 required')
    return g

def components(cells):
    todo=set(cells);out=[]
    while todo:
        p=min(todo);todo.remove(p);obj={p};stack=[p]
        while stack:
            r,c=stack.pop()
            for dr,dc in D4:
                q=r+dr,c+dc
                if q in todo:todo.remove(q);obj.add(q);stack.append(q)
        out.append(obj)
    return out

def normalize(cells):
    cells=tuple(cells)
    r0=min(r for r,c in cells);c0=min(c for r,c in cells)
    return tuple(sorted((r-r0,c-c0)for r,c in cells))

def rotations(cells):
    cur=normalize(cells);out=[]
    for _ in range(4):
        if cur not in out:out.append(cur)
        cur=normalize((c,-r)for r,c in cur)
    return out

def parse(g):
    grid(g)
    pieces=components((r,c)for r,row in enumerate(g)for c,v in enumerate(row)if v)
    keyed=[p for p in pieces if len({g[r][c]for r,c in p})>1]
    if len(keyed)!=1:raise ValueError('Exactly one multicolored key-bearing piece required')
    anchor=keyed[0]
    base=Counter(g[r][c]for r,c in anchor).most_common(1)[0][0]
    ink=[(r,c)for r,c in anchor if g[r][c]!=base]
    r0=min(r for r,c in ink);r1=max(r for r,c in ink);c0=min(c for r,c in ink);c1=max(c for r,c in ink)
    k=r1-r0+1
    if k!=c1-c0+1 or not 2<=k<=3 or len(pieces)!=k*k:raise ValueError('Square key and matching piece count required')
    key=[g[r][c]for r in range(r0,r1+1)for c in range(c0,c1+1)]
    if len(set(key))!=len(key) or base in key:raise ValueError('Key entries must be distinct from each other and its backing color')
    repaired=anchor|{(r,c)for r in range(r0,r1+1)for c in range(c0,c1+1)}
    shapes=[normalize(repaired)]+[normalize(p)for p in pieces if p is not anchor]
    area=sum(map(len,shapes));n=isqrt(area)
    if n*n!=area:raise ValueError('Repaired pieces do not tile a square area')
    if any(max(r for r,c in p)>=n or max(c for r,c in p)>=n for p in shapes):raise ValueError('Piece larger than target')
    return shapes,key,k,n

def arrangements(g,limit=2):
    """Exact cover with fixed anchor orientation and clockwise rotations elsewhere.

    The first uncovered cell must be the earliest cell of the next piece. The
    assembled piece centroids define k rows and k columns within each row; the
    key assigns their colors. Search stops after `limit` distinct renderings.
    """
    shapes,key,k,n=parse(g)
    full=(1<<(n*n))-1
    def placement(cells):
        if any(not 0<=r<n or not 0<=c<n for r,c in cells):return None
        mask=sum(1<<(r*n+c)for r,c in cells)
        return mask,cells
    first=placement(shapes[0])
    if first is None or (0,0) not in first[1]:raise ValueError('Keyed piece must anchor the upper-left corner')
    variants=[rotations(p)for p in shapes]
    found=[];seen=set();nodes=0
    def visit(occupied,remaining,placed):
        nonlocal nodes
        nodes+=1
        if nodes>300000:raise ValueError('Bounded jigsaw search exhausted')
        if occupied==full:
            result=[[0]*n for _ in range(n)]
            rows=sorted(placed,key=lambda p:sum(r for r,c in p[1])/len(p[1]))
            ordered=[]
            for j in range(k):ordered.extend(sorted(rows[j*k:(j+1)*k],key=lambda p:sum(c for r,c in p[1])/len(p[1])))
            for slot,(_,cells) in enumerate(ordered):
                for r,c in cells:result[r][c]=key[slot]
            sig=tuple(map(tuple,result))
            if sig not in seen:seen.add(sig);found.append((result,placed))
            return len(found)>=limit
        gap=(full^occupied);index=(gap & -gap).bit_length()-1;fr,fc=divmod(index,n)
        for i in remaining:
            for shape in variants[i]:
                dc=fc-shape[0][1]
                cells=tuple((r+fr,c+dc)for r,c in shape)
                p=placement(cells)
                if p is not None and not occupied&p[0]:
                    if visit(occupied|p[0],tuple(j for j in remaining if j!=i),placed+(p,)):return True
        return False
    visit(first[0],tuple(range(1,len(shapes))),(first,))
    return found

def assemble(g):
    solutions=arrangements(g,limit=1)
    if not solutions:raise ValueError('No complete key-compatible jigsaw assembly')
    return solutions[0][0]


def mark(source, threshold=3, diagonal=False, mask_source=None):
    """Recolor a cell iff its closed neighborhood contains threshold colors."""
    g=source if mask_source is None else mask_source
    h,w=len(g),len(g[0]);out=[row[:]for row in source]
    ds=tuple((r,c)for r in (-1,0,1)for c in (-1,0,1)) if diagonal else ((0,0),)+D4
    for r in range(h):
        for c in range(w):
            values={g[r+dr][c+dc]for dr,dc in ds if 0<=r+dr<h and 0<=c+dc<w}
            if len(values)>=threshold:out[r][c]=9
    return out


# An alternate stage deliberately consumes the completed assembled image.

def solve(g,finish='assemble'):
    if finish not in ('assemble','mark_junctions'):raise ValueError('Unknown finish')
    result=assemble(g)
    return result if finish=='assemble' else mark(result)


def integer(value,low,high,name):
    if type(value)is not int or not low<=value<=high:raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def _make_scene(seed,index,attempt):
    import hashlib,random
    rng=random.Random(int.from_bytes(hashlib.sha256(f'jigsaw:{seed}:{index}:{attempt}'.encode()).digest(),'big'))
    k=3 if index in (1,4,8,9) else 2
    b=5 if k==3 else (5+(index%3))
    n=k*b
    cuts=[[0]+[j*b+rng.choice((-1,0,1))for j in range(1,k)]+[n]for _ in range(k)]
    # Opposite offsets produce distinct T junctions rather than a regular cross.
    cuts[0][1]=b-1;cuts[1][1]=b+1
    board=[[next(i*k+j for j in range(k) if cuts[i][j]<=c<cuts[i][j+1])
            for c in range(n)]for i in range(k)for _ in range(b)]
    # Add irregular tabs away from vertices, preserving each piece's connectivity.
    for band in range(k):
        for j in range(1,k):
            c=cuts[band][j];r=band*b+rng.randint(1,b-3)
            col=c if rng.randrange(2) else c-1
            owner=board[r][c-1] if col==c else board[r][c]
            for rr in (r,r+1):board[rr][col]=owner
    for i in range(1,k):
        r=i*b
        candidates=[c for c in range(1,n-2) if len({board[r-1][cc]for cc in range(c-1,c+3)})==1
                    and len({board[r][cc]for cc in range(c-1,c+3)})==1]
        rng.shuffle(candidates)
        for c in candidates[:k]:
            rr=r if rng.randrange(2) else r-1;owner=board[r-1][c] if rr==r else board[r][c]
            board[rr][c]=owner;board[rr][c+1]=owner
    objects=[{(r,c)for r in range(n)for c in range(n)if board[r][c]==j}for j in range(k*k)]
    if any(len(components(p))!=1 for p in objects):return None
    # The guide must be entirely in the solid interior of the anchor piece.
    if not all((r,c)in objects[0]for r in range(1,k+1)for c in range(1,k+1)):return None
    pigments=rng.sample(list(range(1,10)),k*k);backing=pigments[0]
    palette=rng.sample([c for c in range(10)if c!=backing],k*k)
    patches=[]
    for j,obj in enumerate(objects):
        shape=normalize(obj)
        if j:shape=rng.choice(rotations(shape))
        ph=max(r for r,c in shape)+1;pw=max(c for r,c in shape)+1
        patch=[[0]*pw for _ in range(ph)]
        for r,c in shape:patch[r][c]=pigments[j]
        if not j:
            for r in range(k):
                for c in range(k):patch[r+1][c+1]=palette[r*k+c]
        patches.append(patch)
    maxh=max(map(len,patches));maxw=max(len(p[0])for p in patches)
    min_h=k*(maxh+1)+1;min_w=k*(maxw+1)+1
    if max(min_h,min_w)>30:return None
    h=w=30 if index==9 else None
    if index!=9:h=rng.randint(min_h,min(30,min_h+3));w=rng.randint(min_w,min(30,min_w+3))
    g=[[0]*w for _ in range(h)]
    slots=list(range(k*k));rng.shuffle(slots)
    row_offsets=[round(i*(h-maxh-2)/(k-1))+1 for i in range(k)]
    col_offsets=[round(i*(w-maxw-2)/(k-1))+1 for i in range(k)]
    for patch,slot in zip(patches,slots):
        r0=row_offsets[slot//k];c0=col_offsets[slot%k]
        # Bounded positional noise inside each separated scatter slot.
        r0+=rng.randrange(maxh-len(patch)+1);c0+=rng.randrange(maxw-len(patch[0])+1)
        for r,row in enumerate(patch):
            for c,v in enumerate(row):g[r0+r][c0+c]=v
    expected=[[palette[v]for v in row]for row in board]
    try:solutions=arrangements(g,2)
    except ValueError:return None
    if len(solutions)!=1 or solutions[0][0]!=expected:return None
    if mark(expected)==expected:return None
    return tuple(map(tuple,g))


from functools import lru_cache

@lru_cache(maxsize=256)
def _scene(seed,index):
    for attempt in range(96):
        result=_make_scene(seed,index,attempt)
        if result is not None:return result
    raise ValueError(f'No unambiguous jigsaw within 96 attempts: seed={seed}, index={index}')

def scene(seed,index):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'index')
    return [list(row)for row in _scene(seed,index)]
