"""Radial tile reflections and reconstruction of the missing center tile."""
from collections import Counter
import hashlib
import random

DIRECTIONS=[(i,j) for i in (-1,0,1) for j in (-1,0,1) if i or j]


def validate_grid(g):
    if(type(g)is not list or not 1<=len(g)<=30 or type(g[0])is not list or not 1<=len(g[0])<=30
       or any(type(row)is not list or len(row)!=len(g[0]) or any(type(v)is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError("Expected a rectangular integer ARC grid")
    return g


def mode(values):
    counts=Counter(values)
    if not counts:raise ValueError("Empty color population")
    return min(counts,key=lambda x:(-counts[x],x))


def background(g):return mode(v for row in g for v in row)


def rings(g,bg):
    pending={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v!=bg};result=[]
    while pending:
        p=min(pending);pending.remove(p);cells={p};queue=[p]
        while queue:
            r,c=queue.pop()
            for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                q=r+dr,c+dc
                if q in pending:pending.remove(q);cells.add(q);queue.append(q)
        r0=min(r for r,c in cells);c0=min(c for r,c in cells)
        if max(r for r,c in cells)-r0!=8 or max(c for r,c in cells)-c0!=8:
            raise ValueError("Each motif must be a 9x9 ring of 3x3 tiles")
        expected={(r0+r,c0+c) for r in range(9) for c in range(9) if not (3<=r<=5 and 3<=c<=5)}
        if cells!=expected:raise ValueError("Expected a blank 3x3 center and eight complete tiles")
        result.append((r0,c0,mode(g[r][c] for r,c in cells)))
    if not result:raise ValueError("No radial motifs")
    return result


def expand(g):
    validate_grid(g);bg=background(g);motifs=rings(g,bg);out=[row[:] for row in g]
    for r0,c0,base in motifs:
        # Reflect each tile across the corresponding outer side/corner.
        for dr,dc in DIRECTIONS:
            sr,sc=r0+3*(dr+1),c0+3*(dc+1)
            tr,tc=r0+3*(2*dr+1),c0+3*(2*dc+1)
            for i in range(3):
                for j in range(3):
                    r,c=tr+i,tc+j
                    if 0<=r<len(g) and 0<=c<len(g[0]):
                        out[r][c]=g[sr+(2-i if dr else i)][sc+(2-j if dc else j)]
            # The inward-facing tip supplies the corresponding center cell.
            i=2 if dr<0 else 0 if dr>0 else 1
            j=2 if dc<0 else 0 if dc>0 else 1
            out[r0+4+dr][c0+4+dc]=g[sr+i][sc+j]
        out[r0+4][c0+4]=base
    return out


def recolor_selected(stage,bg,motifs,colors):
    out=[row[:] for row in stage];marker=0 if bg==9 else 9
    for (r0,c0,base),color in zip(motifs,colors):
        for r in range(max(0,r0-3),min(len(out),r0+12)):
            for c in range(max(0,c0-3),min(len(out[0]),c0+12)):
                if stage[r][c]==color:out[r][c]=marker
    return out


def solve(g,finish="expand"):
    if finish not in ("expand","center_majority"):raise ValueError("Unknown finish")
    stage=expand(g)
    if finish=="expand":return stage
    bg=background(g);motifs=rings(g,bg)
    colors=[mode(stage[r+4+dr][c+4+dc] for dr,dc in DIRECTIONS) for r,c,_ in motifs]
    return recolor_selected(stage,bg,motifs,colors)


def stream(seed,tag):
    return random.Random(int.from_bytes(hashlib.sha256(f"{seed}:{tag}".encode()).digest(),"big"))


def paint_ring(grid,r0,c0,rng,phase):
    bg=grid[0][0];marker=0 if bg==9 else 9
    palette=rng.sample([c for c in range(10) if c not in (bg,marker)],4)
    base=palette[0];low,target,high=sorted(palette[1:]);other,accent=(high,low) if phase%2==0 else (low,high)
    tips=[target]*rng.choice([5,6]);tips += [other]*(8-len(tips));rng.shuffle(tips)
    # Force a misleading corner while preserving the chosen frequency.
    if tips[0]==target:
        j=tips.index(other);tips[0],tips[j]=tips[j],tips[0]
    if phase%3==0:decoration=[other]*23+[accent]
    elif phase%3==1:decoration=[target]*13+[other]*6+[accent]*5
    else:decoration=[other]*12+[accent]*12
    rng.shuffle(decoration)
    for k,(dr,dc) in enumerate(DIRECTIONS):
        sr,sc=r0+3*(dr+1),c0+3*(dc+1)
        tip=(2 if dr<0 else 0 if dr>0 else 1,2 if dc<0 else 0 if dc>0 else 1)
        positions=[(i,j) for i in range(3) for j in range(3) if (i,j)!=tip];rng.shuffle(positions)
        for i in range(3):
            for j in range(3):grid[sr+i][sc+j]=base
        for (i,j),v in zip(positions[:3],decoration[3*k:3*k+3]):grid[sr+i][sc+j]=v
        grid[sr+tip[0]][sc+tip[1]]=tips[k]


def scene(seed,index,query=False):
    rng=stream(seed,f"{'query' if query else 'demo'}:{index}")
    height,width=([(18,22),(23,25),(27,28),(30,30)][index] if query else (18+index%3,19+index%4))
    bg=rng.randrange(10);grid=[[bg]*width for _ in range(height)]
    if query and index==3:
        origins=[(3,3),(3,18),(18,3),(18,18)]
    else:
        origins=[(rng.randrange(3,height-11),rng.randrange(3,width-11))]
        if query and index==2:origins=[(1,width-10)]  # lawful clipping of outer reflections
    for k,(r,c) in enumerate(origins):paint_ring(grid,r,c,rng,index+k)
    return grid
