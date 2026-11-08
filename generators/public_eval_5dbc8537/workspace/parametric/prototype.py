"""Translation-only colored-piece packing, with an optional solution-selected frame."""
from collections import Counter
from collections import deque


def validate_grid(grid):
    if not isinstance(grid,list) or not 1<=len(grid)<=30 or not isinstance(grid[0],list) or not 1<=len(grid[0])<=30:
        raise ValueError('grid must have dimensions 1..30')
    if any(not isinstance(row,list) or len(row)!=len(grid[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid):
        raise ValueError('rectangular integer-color grid required')


def mode(values):
    counts=Counter(values)
    return min(counts,key=lambda x:(-counts[x],x))


def components(cells, diagonal=True):
    todo=set(cells); out=[]
    steps=[(r,c) for r in (-1,0,1) for c in (-1,0,1) if (r or c) and (diagonal or not r or not c)]
    while todo:
        p=min(todo); todo.remove(p); q=deque([p]); comp=[p]
        while q:
            r,c=q.popleft()
            for dr,dc in steps:
                n=(r+dr,c+dc)
                if n in todo:
                    todo.remove(n);q.append(n);comp.append(n)
        out.append(sorted(comp))
    return out


def parse(grid):
    validate_grid(grid)
    bg=mode(v for row in grid for v in row)
    counts=Counter(v for row in grid for v in row if v!=bg)
    if not counts: raise ValueError('target frame is missing')
    frame=min(counts,key=lambda x:(-counts[x],x))
    cells=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==frame]
    r0=min(r for r,c in cells);r1=max(r for r,c in cells)
    c0=min(c for r,c in cells);c1=max(c for r,c in cells)
    board=[row[c0:c1+1] for row in grid[r0:r1+1]]
    if any(v not in (bg,frame) for row in board for v in row):
        raise ValueError('target contains a foreign color')
    outside={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v!=bg and not(r0<=r<=r1 and c0<=c<=c1)}
    pieces=[]
    for comp in components(outside):
        a=min(r for r,c in comp);b=min(c for r,c in comp)
        z=max(r for r,c in comp);t=max(c for r,c in comp)
        if len(comp)!=(z-a+1)*(t-b+1):
            raise ValueError('source pieces must be solid colored rectangles')
        pieces.append([row[b:t+1] for row in grid[a:z+1]])
    return bg,frame,board,pieces


def pack(board,pieces,bg,require_unique=False):
    """Exact cover with row-major first-hole branching; no rotation or reflection.

    Returns the filled board and placement records (row, column, piece grid).
    Uniqueness is output uniqueness: identical inventory copies may permute.
    """
    holes=frozenset((r,c) for r,row in enumerate(board) for c,v in enumerate(row) if v==bg)
    if sum(len(p)*len(p[0]) for p in pieces)!=len(holes):
        raise ValueError('piece area does not cover target')
    solutions=[];seen_outputs=set();nodes=0
    def visit(remaining,inventory,records):
        nonlocal nodes
        nodes+=1
        if nodes>200000:raise ValueError('exact cover search budget exceeded')
        if not remaining:
            out=[row[:] for row in board]
            for r,c,p in records:
                for a,row in enumerate(p):
                    out[r+a][c:c+len(row)]=row
            sig=tuple(map(tuple,out))
            if sig not in seen_outputs:
                seen_outputs.add(sig);solutions.append((out,records))
            return len(solutions)>=(2 if require_unique else 1)
        r,c=min(remaining);tried=set()
        for i,p in enumerate(inventory):
            sig=tuple(map(tuple,p))
            if sig in tried:continue
            tried.add(sig)
            used=frozenset((r+a,c+b) for a in range(len(p)) for b in range(len(p[0])))
            if used<=remaining and visit(remaining-used,inventory[:i]+inventory[i+1:],records+[(r,c,p)]):
                return True
        return False
    visit(holes,list(pieces),[])
    if not solutions:raise ValueError('no exact cover')
    if require_unique and len(solutions)>1:raise ValueError('ambiguous exact cover')
    return solutions[0]


def solve(grid,frame_policy='original',require_unique=False):
    if frame_policy not in ('original','first_placed_piece','last_placed_piece'):
        raise ValueError('invalid frame_policy')
    bg,frame,board,pieces=parse(grid)
    out,records=pack(board,pieces,bg,require_unique)
    if frame_policy!='original':
        if not records:raise ValueError('at least one placed piece required')
        selected=records[0 if frame_policy=='first_placed_piece' else -1][2]
        color=mode(v for row in selected for v in row)
        out=[[color if board[r][c]==frame else v for c,v in enumerate(row)] for r,row in enumerate(out)]
    return out
