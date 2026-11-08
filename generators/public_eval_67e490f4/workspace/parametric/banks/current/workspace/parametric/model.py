"""Fill template holes using per-shape color frequency among external glyphs.
Shapes match up to translation, rotation and reflection, without scaling.
"""
from __future__ import annotations
from collections import Counter
from functools import lru_cache
import random
RULE_TASK_ID = 'ee_67e490f4'

def components(g, same=True, diagonal=False, background=None):
    h,w=len(g),len(g[0]);seen=set();result=[]
    for r in range(h):
        for c in range(w):
            if (r,c) in seen or g[r][c]==background:continue
            stack=[(r,c)];seen.add((r,c));cells=[];color=g[r][c]
            while stack:
                x,y=stack.pop();cells.append((x,y))
                for dx,dy in ((-1,0),(1,0),(0,-1),(0,1))+(((-1,-1),(-1,1),(1,-1),(1,1)) if diagonal else ()):
                    a,b=x+dx,y+dy
                    if 0<=a<h and 0<=b<w and (a,b) not in seen and g[a][b]!=background and (not same or g[a][b]==color):
                        seen.add((a,b));stack.append((a,b))
            result.append(sorted(cells))
    return result


def bbox(cells):
    return min(r for r,c in cells),min(c for r,c in cells),max(r for r,c in cells),max(c for r,c in cells)


def inside(p,b):
    return b[0]<=p[0]<=b[2] and b[1]<=p[1]<=b[3]


def rim(b):
    a,b0,z,d=b
    return [(r,c) for r in range(a,z+1) for c in range(b0,d+1) if r in (a,z) or c in (b0,d)]



def normalize(cells):
    a,b,_,_=bbox(cells)
    return tuple(sorted((r-a,c-b) for r,c in cells))

@lru_cache(maxsize=4096)
def orientations(shape):
    result=[]
    for flip in (False,True):
        cells=[(r,-c if flip else c) for r,c in shape]
        for turn in range(4):
            result.append(normalize(cells));cells=[(c,-r) for r,c in cells]
    return tuple(sorted(set(result)))

def key(cells):return min(orientations(normalize(cells)))

def rotations(cells):
    out=[]
    for _ in range(4):out.append(normalize(cells));cells=[(c,-r) for r,c in cells]
    return tuple(out)

def records(g):
    bg=Counter(v for row in g for v in row).most_common(1)[0][0]
    objects=components(g,diagonal=True,background=bg)
    frame=max(objects,key=len);f=bbox(frame);fc=g[frame[0][0]][frame[0][1]]
    cropped=[row[f[1]:f[3]+1] for row in g[f[0]:f[2]+1]]
    holes=components(cropped,background=fc)
    external=[o for o in objects if not any(inside(p,f) for p in o)]
    counts={};all_counts=Counter()
    for o in external:
        color=g[o[0][0]][o[0][1]];k=key(o)
        counts.setdefault(k,Counter())[color]+=1;all_counts[color]+=1
    return cropped,holes,counts,external,all_counts

def solve(g,policy='most_frequent',rival=None):
    if policy not in ('most_frequent','least_frequent'):raise ValueError('unknown vote policy')
    out,holes,counts,external,all_counts=records(g)
    for cells in holes:
        k=key(cells)
        votes=counts.get(k,{})
        if rival=='area_only':
            votes=Counter()
            for kk,cc in counts.items():
                if len(kk)==len(k):votes.update(cc)
        if rival in ('orientation_exact','rotations_only','bbox_only'):
            votes=Counter()
            for obj in external:
                shape=normalize(obj);want=normalize(cells)
                if rival=='orientation_exact':matched=shape==want
                elif rival=='bbox_only':
                    b1=bbox(shape);b2=bbox(want)
                    matched=sorted((b1[2]+1,b1[3]+1))==sorted((b2[2]+1,b2[3]+1))
                else:
                    turns=[]
                    for _ in range(4):turns.append(normalize(shape));shape=tuple((c,-r) for r,c in shape)
                    matched=want in turns
                if matched:votes[g[obj[0][0]][obj[0][1]]]+=1
        if not votes:continue
        if rival=='global_frequency':votes={c:all_counts[c] for c in votes}
        if rival=='pixel_frequency':votes={c:sum(len(o) for o in external if g[o[0][0]][o[0][1]]==c) for c in votes}
        score=(min if policy=='least_frequent' else max)(votes.values())
        winners=[c for c in votes if votes[c]==score]
        if rival=='smallest_color':winners=list(votes)
        if rival=='largest_color':color=max(votes)
        elif rival=='largest_tie':color=max(winners)
        elif rival=='first_source':
            color=next(g[o[0][0]][o[0][1]] for o in external if key(o)==k)
        elif rival=='last_source':
            color=next(g[o[0][0]][o[0][1]] for o in external[::-1] if key(o)==k)
        else:color=min(winners)
        for r,c in cells:out[r][c]=color
    return out

SHAPES=(
 ((0,0),(1,0),(1,1)),
 ((0,0),(1,0),(2,0)),
 ((0,1),(1,0),(1,1),(1,2),(2,1)),
 ((0,0),(1,0),(2,0),(2,1),(2,2)),
 ((0,0),(1,0),(2,0),(2,1)),
 ((0,0),(0,1),(0,2),(1,1)),
 ((0,1),(0,2),(1,0),(1,1)),
 ((0,0),(0,1),(1,0),(1,1)),
 ((0,0),),
 ((0,0),(0,1)),
)


def scene(seed,index):
    rng=random.Random(f'67e490f4:{seed}:{index}')
    h,w=((20,24),(24,24),(24,28),(28,28))[index%4]
    if index==9:h=w=30
    colors=list(range(10));rng.shuffle(colors);bg,fc=colors[:2];palette=colors[2:5]
    shapes=[SHAPES[i] for i in ([2,3,4] if index==0 else [0,1,6] if index==1 else rng.sample(range(len(SHAPES)),3))]
    g=[[bg]*w for _ in range(h)]
    for r in range(13):
        for c in range(9):g[r][c]=fc
    order=[0,1,2,0,1,2];rng.shuffle(order)
    for cell,which in enumerate(order):
        r,c=1+4*(cell//2),1+4*(cell%2)
        # Chiral L4 holes are mirrored relative to every external L4 exemplar.
        options=rotations([(r,-c) for r,c in shapes[which]]) if index==0 and which==2 else orientations(shapes[which])
        shape=rng.choice(options)
        for dr,dc in shape:g[r+dr][c+dc]=bg
    matrix=((3,1,2),(2,3,1),(1,2,3)) if index%2==0 else ((2,2,1),(1,2,2),(2,1,2))
    glyphs=[]
    for which,votes in enumerate(matrix):
        for color,n in zip(palette,votes):
            for j in range(n):
                options=rotations(shapes[which]) if index==0 and which==2 else orientations(shapes[which])
                glyphs.append((rng.choice(options),color))
    slots=[(r,c) for r in range(0,h-2,4) for c in range(0,w-2,4) if not (r<16 and c<12)]
    if len(slots)<len(glyphs):raise ValueError('insufficient non-touching glyph slots')
    rng.shuffle(slots);rng.shuffle(glyphs)
    for (shape,color),(r,c) in zip(glyphs,slots):
        for dr,dc in shape:g[r+dr][c+dc]=color
    if index%2:g=[list(row) for row in zip(*g)]
    if rng.randrange(2):g=g[::-1]
    if rng.randrange(2):g=[row[::-1] for row in g]
    return g


def generate(seed=0,sample_index=0,difficulty='medium'):
    if type(seed) is not int or type(sample_index) is not int or sample_index<0:raise ValueError('integer seed and nonnegative sample index required')
    return scene(seed,sample_index)


def self_check(g,difficulty='medium'):
    try:
        if not g or not g[0] or any(len(row)!=len(g[0]) for row in g):raise ValueError('nonempty rectangular grid required')
        if not 1<=len(g)<=30 or not 1<=len(g[0])<=30:raise ValueError('grid outside 1..30')
        if any(type(v) is not int or not 0<=v<=9 for row in g for v in row):raise ValueError('exact integer colors required')
        crop,holes,counts,external,_=records(g)
        if not holes or not external or any(key(x) not in counts for x in holes):raise ValueError('unmatched template hole')
        return []
    except (ValueError,TypeError,IndexError) as exc:return [str(exc)]
