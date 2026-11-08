"""Shape-conditioned color voting, independent oracle and constructive grammar."""
from __future__ import annotations
from collections import Counter
from functools import lru_cache
import copy
import hashlib
import random


def integer(value,low,high,name):
    if type(value) is not int or not low<=value<=high:raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def grid_check(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30
        or any(type(row) is not list or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row)for row in g)):
        raise ValueError('Expected a rectangular exact-color grid of size 1..30')
    return g


def components(g,bg):
    seen=set();objects=[];h,w=len(g),len(g[0])
    for r in range(h):
        for c in range(w):
            if g[r][c]==bg or(r,c)in seen:continue
            color=g[r][c];stack=[(r,c)];seen.add((r,c));cells=[]
            while stack:
                a,b=stack.pop();cells.append((a,b))
                for i,j in ((a-1,b),(a+1,b),(a,b-1),(a,b+1)):
                    if 0<=i<h and 0<=j<w and(i,j)not in seen and g[i][j]==color:
                        seen.add((i,j));stack.append((i,j))
            objects.append({'color':color,'cells':tuple(sorted(cells))})
    return objects


def normalize(cells):
    cells=tuple(cells)
    if not cells:raise ValueError('Empty shape')
    r0=min(r for r,c in cells);c0=min(c for r,c in cells)
    return tuple(sorted((r-r0,c-c0)for r,c in cells))


def transform(cells,index):
    points=[(r,-c if index>=4 else c)for r,c in cells]
    for _ in range(index%4):points=[(c,-r)for r,c in points]
    return normalize(points)


@lru_cache(maxsize=512)
def _key(shape):return min(transform(shape,i)for i in range(8))

def shape_key(cells):return _key(normalize(cells))


def choose_color(counts,vote):
    if not counts:raise ValueError('No matching exemplar')
    if vote not in ('most_frequent','least_frequent'):raise ValueError('Unknown vote')
    return min(counts,key=lambda c:((-counts[c]if vote=='most_frequent'else counts[c]),c))


def analyze(g):
    grid_check(g);counts=Counter(v for row in g for v in row);bg=min(counts,key=lambda c:(-counts[c],c))
    objects=components(g,bg)
    if not objects:raise ValueError('No panel')
    panel=max(objects,key=lambda o:len(o['cells']))
    if sum(len(o['cells'])==len(panel['cells'])for o in objects)!=1:raise ValueError('Largest panel must be unique')
    cells=panel['cells'];r0=min(r for r,c in cells);r1=max(r for r,c in cells);c0=min(c for r,c in cells);c1=max(c for r,c in cells)
    canvas=[row[c0:c1+1]for row in g[r0:r1+1]];pc=panel['color']
    if any(v not in (pc,bg)for row in canvas for v in row):raise ValueError('Panel contains nonbackground foreign cells')
    holes=[o['cells']for o in components(canvas,pc)]
    if not holes:raise ValueError('Panel must contain a hole')
    clues=[o for o in objects if all(not(r0<=r<=r1 and c0<=c<=c1)for r,c in o['cells'])]
    votes={}
    for o in clues:votes.setdefault(shape_key(o['cells']),Counter())[o['color']]+=1
    if any(shape_key(h)not in votes for h in holes):raise ValueError('Hole has no matching shape exemplar')
    return dict(bg=bg,panel_color=pc,bounds=(r0,c0,r1,c1),canvas=canvas,holes=holes,clues=clues,votes=votes)


def render(info,colors):
    out=copy.deepcopy(info['canvas'])
    for hole,color in zip(info['holes'],colors):
        for r,c in hole:out[r][c]=color
    return out


def solve(g,vote='most_frequent'):
    info=analyze(g)
    return render(info,[choose_color(info['votes'][shape_key(hole)],vote)for hole in info['holes']])


# First three shapes deliberately have equal area but inequivalent geometry.
SHAPES=( ((0,0),(1,0),(2,0),(2,1)),
         ((0,0),(0,1),(1,0),(1,1)),
         ((0,0),(0,1),(0,2),(1,1)),
         ((0,1),(1,0),(1,1),(1,2),(2,1)),
         ((0,0),(0,1)),
         ((0,0),(1,0),(1,1)) )


def rng_for(seed,tag):return random.Random(int.from_bytes(hashlib.sha256(f'{seed}:shape-votes:{tag}'.encode()).digest(),'big'))


def sample_grid(seed,tag,profile):
    """Height,width,panel-height,panel-width,class-count,frequency profile."""
    h,w,ph,pw,nclasses,counts_profile=profile;rng=rng_for(seed,tag)
    bg,pc,*palette=rng.sample(range(10),5)
    r0=0 if pw==w else rng.choice((0,h-ph));c0=0 if pw==w else rng.choice((0,w-pw))
    g=[[bg]*w for _ in range(h)]
    for r in range(r0,r0+ph):
        for c in range(c0,c0+pw):g[r][c]=pc
    hole_slots=[(r,c)for r in range(1,ph-3,4)for c in range(1,pw-3,4)]
    if len(hole_slots)<nclasses+1:raise ValueError('Too few separated hole slots')
    # Repeated chiral class zero has both handednesses, making rotation-only
    # matching visibly insufficient for BOTH majority and minority settings.
    identities=list(range(nclasses))+[0]+[i%nclasses for i in range(len(hole_slots)-nclasses-1)]
    rng.shuffle(identities);seen=Counter()
    for (r,c),i in zip(hole_slots,identities):
        orientation=(0 if seen[i]%2==0 else 4)if i==0 else rng.randrange(8)
        seen[i]+=1
        for dr,dc in transform(SHAPES[i],orientation):g[r0+r+dr][c0+c+dc]=bg
    sequences=[]
    for i in range(nclasses):
        major=palette[i%3];minor=palette[(i+1)%3];middle=palette[(i+2)%3]
        seq=([major,minor,major]if counts_profile==0 else
             [minor,major,major,major,minor]if counts_profile==1 else
             [major,middle,minor,major,middle,major])
        sequences.append(seq)
    # Interleave classes while preserving the first/last-color diagnostic per class.
    order=list(range(nclasses));rng.shuffle(order);clues=[]
    for j in range(max(map(len,sequences))):
        for i in order:
            if j>=len(sequences[i]):continue
            color=sequences[i][j]
            k=rng.randrange(4)+(0 if color==palette[i%3] else 4)if i==0 else rng.randrange(8)
            clues.append((color,transform(SHAPES[i],k)))
    slots=[(r,c)for r in range(0,h-2,4)for c in range(0,w-2,4)
           if r+2<r0-1 or r>r0+ph or c+2<c0-1 or c>c0+pw]
    if len(slots)<len(clues):raise ValueError(f'Insufficient gallery slots: {len(slots)} for {len(clues)}')
    slots=sorted(rng.sample(slots,len(clues)))
    for (r,c),(color,shape)in zip(slots,clues):
        for dr,dc in shape:g[r+dr][c+dc]=color
    info=analyze(g)
    if info['bg']!=bg or info['panel_color']!=pc or len(info['clues'])!=len(clues):raise ValueError('Scene grammar mismatch')
    return g


@lru_cache(maxsize=128)
def _bank(seed):
    ds=[(22,26,9,13,3,0),(30,29,9,17,6,1),(26,26,9,13,3,2),
        (28,29,13,13,4,1),(29,30,9,17,5,0),(30,27,9,13,4,2)]
    qs=[(24,26,9,13,3,1),(28,30,13,13,4,0),(30,28,9,17,5,0),(30,30,7,30,6,1)]
    train=[sample_grid(seed,f'demo:{i}',p)for i,p in enumerate(ds)]
    queries=[sample_grid(seed,f'query:{i}',p)for i,p in enumerate(qs)]
    rng_for(seed,'presentation').shuffle(queries)
    return train,queries


def bank(seed):return copy.deepcopy(_bank(seed))
