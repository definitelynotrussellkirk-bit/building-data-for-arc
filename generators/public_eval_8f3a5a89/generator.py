"""Self-contained ordinary generator for unapproved public parent 8f3a5a89."""
from __future__ import annotations
from collections import deque
import hashlib, json, random

RULE_TASK_ID = 'ee_8f3a5a89'
TASK_ID = 'public_eval_8f3a5a89'
MIN_TRAIN = 2
MAX_TRAIN = 6
BG, WALL, SEED, OUTLINE = 8, 1, 6, 7
D4 = ((-1,0),(1,0),(0,-1),(0,1))
D8 = tuple((a,b) for a in (-1,0,1) for b in (-1,0,1) if (a,b)!=(0,0))

def integer(v,lo,hi,name):
    if type(v) is not int or not lo<=v<=hi: raise ValueError(f'{name} must be integer in range')
    return v

def _components(cells):
    rem=set(cells); out=[]
    while rem:
        s=min(rem); rem.remove(s); comp={s}; q=deque([s])
        while q:
            r,c=q.popleft()
            for dr,dc in D4:
                p=(r+dr,c+dc)
                if p in rem: rem.remove(p);comp.add(p);q.append(p)
        out.append(comp)
    return out

def analyze(g):
    h=len(g);w=len(g[0]); seeds=[(r,c)for r in range(h)for c in range(w)if g[r][c]==6]
    if len(seeds)!=1: raise ValueError('one seed required')
    trav={(r,c)for r in range(h)for c in range(w)if g[r][c]in(8,6)}
    region=next(x for x in _components(trav) if seeds[0] in x)
    allc={(r,c)for r in range(h)for c in range(w)}
    comps=_components(allc-region)
    holes=[x for x in comps if not any(r in(0,h-1)or c in(0,w-1)for r,c in x)]
    hc=set().union(*holes)if holes else set()
    walls={(r,c)for r in range(h)for c in range(w)if g[r][c]==1}; keep=set()
    for comp in _components(walls):
        if any((r+dr,c+dc)in region for r,c in comp for dr,dc in D4):keep|=comp
    return region,hc,keep,seeds[0]

def rule_mirror(g):
    h=len(g);w=len(g[0]);region,holes,keep,seed=analyze(g);domain=region|holes
    out=[[8]*w for _ in range(h)]
    for r,c in holes|keep:out[r][c]=g[r][c]
    for r,c in region:
        if (r,c)==seed:out[r][c]=6;continue
        out[r][c]=7 if any(not(0<=r+dr<h and 0<=c+dc<w)or(r+dr,c+dc)not in domain for dr,dc in D8) else 8
    return out

def _rng(seed,tag):
    return random.Random(int.from_bytes(hashlib.sha256(json.dumps([seed,tag],sort_keys=True).encode()).digest()[:16],'big'))
def _rect(g,r,c,a,b,v=1):
    for i in range(r,r+a):
        for j in range(c,c+b):g[i][j]=v
def _scene(seed,tag,h,w,vertical=True,stress=False):
    rng=_rng(seed,tag);g=[[8]*w for _ in range(h)]
    if vertical:
        s=max(7,min(w-5,w//2+rng.choice((-1,0,1))))
        for r in range(h):g[r][s]=1
        rr=max(3,min(h-4,h//2+rng.choice((-2,1))))
        for c in range(s-2-int(stress),s):g[rr][c]=1
        g[h-1][0]=6;_rect(g,2,2,2,2+int(stress));br=max(6,min(h-4,h//2+2));bc=2+seed%2
        for dr,dc in ((0,0),(1,0),(1,1),(2,1)):
            if br+dr<h-1 and bc+dc<s-1:g[br+dr][bc+dc]=1
        _rect(g,1,min(w-3,s+2),2,2)
        if stress:_rect(g,h-5,min(w-4,s+2),3,2)
    else:
        s=max(7,min(h-5,h//2+rng.choice((-1,0,1))))
        for c in range(w):g[s][c]=1
        cc=max(3,min(w-4,w//2+rng.choice((-2,1))))
        for r in range(s-2-int(stress),s):g[r][cc]=1
        g[0][0]=6;_rect(g,2,2,2+int(stress),2);br=2+seed%2;bc=max(6,min(w-4,w//2+2))
        for dr,dc in ((0,0),(0,1),(1,1),(1,2)):
            if br+dr<s-1 and bc+dc<w-1:g[br+dr][bc+dc]=1
        _rect(g,min(h-3,s+2),1,2,2)
        if stress:_rect(g,min(h-4,s+2),w-5,2,3)
    return g

def generate(seed,sample_index=0,difficulty=None):
    integer(seed,0,2**63-1,'seed');integer(sample_index,0,2**31-1,'sample_index')
    if difficulty not in(None,'easy','medium','hard'):raise ValueError('unknown difficulty')
    hard=difficulty=='hard' or sample_index%4==3
    size=30 if hard else 12+2*(sample_index%6)
    return _scene(seed,['ordinary',sample_index],size,min(30,size+2),sample_index%2==0,hard)
def self_check(g):
    issues=[]
    try:
        region,holes,_,_=analyze(g)
        if not holes:issues.append('no holes')
        if not region:issues.append('empty region')
    except Exception as e:issues.append(str(e))
    return issues
