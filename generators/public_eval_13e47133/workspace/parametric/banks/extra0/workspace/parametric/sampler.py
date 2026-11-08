"""Standalone sparse-cue inward-band scenes with rectangular and concave regions."""
from collections import deque
import hashlib
import random
TASK_ID='public_eval_13e47133'
GENERATOR_ID=TASK_ID
RULE_TASK_ID='ee_13e47133'
VERSION='1.0.0'
EXAMPLES_NEEDED=2
SUMMARY='Recover region-local color cycles from sparse depth cues and fill inward bands.'
AXES={'height':{'type':'int','valid':'20..30'},'width':{'type':'int','valid':'23..30'},'rotation':{'type':'int','valid':'0..3'}}
CARDINAL=((-1,0),(1,0),(0,-1),(0,1))
KING=tuple((r,c) for r in (-1,0,1) for c in (-1,0,1) if r or c)


def _draw_rng(seed, sample_index, label):
    """Mirror the repository's stable keyed RNG without external imports."""
    salt=f"{TASK_ID}|{sample_index}|{label}"
    digest=hashlib.sha256(f"{seed}|{salt}|{VERSION}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16],"big"))


def _regions(cells):
    todo=set(cells);out=[]
    while todo:
        p=min(todo);todo.remove(p);q=deque([p]);component={p}
        while q:
            r,c=q.popleft()
            for dr,dc in CARDINAL:
                n=(r+dr,c+dc)
                if n in todo:todo.remove(n);component.add(n);q.append(n)
        out.append(component)
    return out


def _depths(cells):
    edge=sorted(p for p in cells if any((p[0]+dr,p[1]+dc) not in cells for dr,dc in KING))
    ds={p:0 for p in edge};q=deque(edge)
    while q:
        r,c=q.popleft()
        for dr,dc in KING:
            n=(r+dr,c+dc)
            if n in cells and n not in ds:ds[n]=ds[(r,c)]+1;q.append(n)
    return ds


def generate(seed,sample_index,*,difficulty=None,**overrides):
    if type(seed) is not int or seed<0 or type(sample_index) is not int or sample_index<0:raise ValueError('nonnegative integer seed and sample index required')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('invalid difficulty')
    if set(overrides)-set(AXES):raise ValueError('unknown override')
    rng=_draw_rng(seed,sample_index,'geometry');colors=_draw_rng(seed,sample_index,'palette');cues=_draw_rng(seed,sample_index,'cues')
    height=overrides.get('height',(20,23,26,30)[sample_index%4]);width=overrides.get('width',(23,25,28,30)[sample_index%4]);rotation=overrides.get('rotation',sample_index%4)
    if type(height) is not int or not 20<=height<=30 or type(width) is not int or not 23<=width<=30:raise ValueError('height 20..30 and width 23..30 required')
    if type(rotation) is not int or rotation not in range(4):raise ValueError('rotation must be 0..3')
    bg,wall=colors.sample(range(10),2);g=[[bg]*width for _ in range(height)]
    split=rng.randint(9,width-10)
    for r in range(height):g[r][split]=wall
    top=rng.randint(height//3-1,height//3+1);bottom=top+rng.choice((5,6))
    right=split+rng.choice((5,6))
    for c in range(split,right+1):g[top][c]=g[bottom][c]=wall
    for r in range(top,bottom+1):g[r][right]=wall
    if rng.randrange(2):
        divider=rng.randint(height//2-1,height//2+1)
        for c in range(split):g[divider][c]=wall
    regions=_regions({(r,c) for r in range(height) for c in range(width) if g[r][c]!=wall})
    measured=[(comp,_depths(comp)) for comp in regions]
    largest=max(range(len(measured)),key=lambda i:len(measured[i][0]))
    for i,(comp,ds) in enumerate(measured):
        r0=min(r for r,c in comp);r1=max(r for r,c in comp);c0=min(c for r,c in comp);c1=max(c for r,c in comp)
        concave=len(comp)!=(r1-r0+1)*(c1-c0+1)
        maxdepth=max(ds.values())
        n=min(3,maxdepth+1) if i==largest or concave else colors.randint(1,min(3,maxdepth+1))
        palette=colors.sample([v for v in range(10) if v not in (bg,wall)],n)
        if n>1 and i==largest and sample_index%2==0:palette[0]=bg
        if n==1 and colors.randrange(3)==0:palette[0]=bg
        corner=cues.choice(((r0,c0),(r0,c1),(r1,c0),(r1,c1)))
        for d,color in enumerate(palette):
            cells=sorted(p for p in comp if ds[p]==d)
            chosen=min(cells,key=lambda p:(abs(p[0]-corner[0])+abs(p[1]-corner[1]),p))
            g[chosen[0]][chosen[1]]=color
            # Redundant same-depth markers decouple palette length from cue count.
            if sample_index%2 and d==1 and len(cells)>1:
                other=max(cells,key=lambda p:(abs(p[0]-chosen[0])+abs(p[1]-chosen[1]),p))
                g[other[0]][other[1]]=color
    for _ in range(rotation):g=[list(row) for row in zip(*g[::-1])]
    return g
