"""Task-local geometry claims for wall docking and cavity projection.

The protected Racket programs independently execute all retained label claims.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import hashlib
import random

MODES=('all','largest_hole')
RIVALS=('identity','raw_contact','open_rows','all_holes','first_hole','last_hole',
        'middle_hole','bbox_area','smallest_hole','reverse_tie','other_setting')


def integer(x,lo,hi,name):
    if type(x) is not int or not lo<=x<=hi: raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return x


def grid(value):
    if (type(value) is not list or not 1<=len(value)<=30 or type(value[0]) is not list or not 1<=len(value[0])<=30 or
        any(type(r) is not list or len(r)!=len(value[0]) or any(type(v) is not int or not 0<=v<=9 for v in r) for r in value)):
        raise ValueError('Expected a rectangular 1..30 exact-integer ARC grid')
    return deepcopy(value)


def rng(seed,salt): return random.Random(int.from_bytes(hashlib.sha256(f'{seed}:6e453dd6:{salt}'.encode()).digest(),'big'))


def components(g,color):
    unseen={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==color};out=[]
    while unseen:
        p=min(unseen);unseen.remove(p);stack=[p];cells=[]
        while stack:
            r,c=stack.pop();cells.append((r,c))
            for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if q in unseen: unseen.remove(q);stack.append(q)
        out.append({'cells':sorted(cells),'area':len(cells),'r1':min(r for r,c in cells),'r2':max(r for r,c in cells),
                    'c1':min(c for r,c in cells),'c2':max(c for r,c in cells)})
    return out


def cavities(g,bg,wall):
    h=len(g)
    ls=[o for o in components(g,bg) if o['r1']>0 and o['r2']<h-1 and o['c1']>0 and o['c2']<wall-1]
    for o in ls:
        o['contact_rows']=sorted({r for r,c in o['cells'] if c==wall-2})
        o['bbox_area']=(o['r2']-o['r1']+1)*(o['c2']-o['c1']+1)
    return ls


def analyze(value):
    g=grid(value);h,w=len(g),len(g[0]);counts=Counter(v for row in g for v in row)
    bg=counts.most_common(1)[0][0]
    walls=[c for c in range(w) if all(g[r][c]==5 for r in range(h))]
    if bg in (0,2,5) or len(walls)!=1 or not 3<=walls[0]<=w-2: raise ValueError('Expected one interior vertical gray wall and a distinct background')
    wall=walls[0]
    if any(g[r][c]==5 for r in range(h) for c in range(w) if c!=wall):
        raise ValueError('Gray cells must belong to the unique wall')
    if any(g[r][c]!=bg for r in range(h) for c in range(wall+1,w)) or any(v not in (bg,0,5) for row in g for v in row):
        raise ValueError('Input requires black objects, gray wall, and an empty right strip')
    objs=components(g,0)
    if not objs or any(o['c2']>=wall for o in objs): raise ValueError('All objects must be left of the wall')
    docked=[[bg if v==0 else v for v in row] for row in g];occupied=set()
    for o in objs:
        shift=wall-1-o['c2']
        cells={(r,c+shift) for r,c in o['cells']}
        if occupied&cells: raise ValueError('Docked objects overlap')
        occupied|=cells
        for r,c in cells: docked[r][c]=0
    holes=cavities(docked,bg,wall);eligible=[o for o in holes if o['contact_rows']]
    return {'grid':g,'background':bg,'wall':wall,'objects':objs,'docked':docked,'holes':holes,'eligible':eligible,'eligible_count':len(eligible)}


def solve(value,projection='all',*,strategy=None):
    if projection not in MODES: raise ValueError('Unknown projection')
    a=analyze(value);out=deepcopy(a['docked']);wall=a['wall'];holes=a['eligible']
    if strategy=='raw_contact': holes=[o for o in cavities(a['grid'],a['background'],wall) if o['contact_rows']]
    if strategy=='all_holes':
        holes=deepcopy(a['holes'])
        for o in holes: o['contact_rows']=sorted({r for r,c in o['cells']})
    if strategy=='open_rows':
        rows=[r for r in range(len(out)) if out[r][wall-2]==a['background'] and out[r][wall-1]==0]
    else:
        if projection=='largest_hole' and holes:
            if strategy=='first_hole': holes=[min(holes,key=lambda o:(o['r1'],o['c1']))]
            elif strategy=='last_hole': holes=[max(holes,key=lambda o:(o['r1'],o['c1']))]
            elif strategy=='middle_hole': holes=[sorted(holes,key=lambda o:(o['r1'],o['c1']))[len(holes)//2]]
            elif strategy=='bbox_area': holes=[min(holes,key=lambda o:(-o['bbox_area'],o['r1'],o['c1']))]
            elif strategy=='smallest_hole': holes=[min(holes,key=lambda o:(o['area'],o['r1'],o['c1']))]
            elif strategy=='reverse_tie': holes=[max(holes,key=lambda o:(o['area'],o['r1'],o['c1']))]
            else: holes=[min(holes,key=lambda o:(-o['area'],o['r1'],o['c1']))]
        rows=sorted({r for o in holes for r in o['contact_rows']})
    for r in rows:
        for c in range(wall+1,len(out[0])): out[r][c]=2
    return out


def rival(g,name,projection='largest_hole'):
    if name=='identity': return grid(g)
    if name=='other_setting': return solve(g,MODES[1-MODES.index(projection)])
    return solve(g,projection,strategy=name)


def shape(kind, width=4):
    """Return one connected black object as a mask with genuine cavities."""
    if kind=='ell':
        ih,iw=3,width; hh,ww=ih+2,iw+2
        holes={(r+1,c+1) for r in range(ih) for c in range(iw) if r==ih-1 or c==iw-1}
    elif kind=='big':
        ih,iw=2,width;hh,ww=ih+2,iw+2;holes={(r+1,c+1) for r in range(ih) for c in range(iw)}
    elif kind=='tiny':
        hh,ww=3,4;holes={(1,1),(1,2)}
    elif kind=='hidden':
        ih,iw=3,width;hh,ww=ih+2,iw+3;holes={(r+1,c+1) for r in range(ih) for c in range(iw)}
    elif kind=='open':
        hh,ww=3,width+2;holes={(1,c) for c in range(ww-1)}
    elif kind=='tie_flat':
        hh,ww=3,6;holes={(1,c) for c in range(1,5)}
    elif kind=='tie_square':
        hh,ww=4,4;holes={(r,c) for r in (1,2) for c in (1,2)}
    elif kind=='double':
        hh,ww=6,10;holes={(r,c) for r in (1,2,3) for c in (1,2,3)}|{(4,7),(4,8)}
    else: raise ValueError('Unknown shape')
    return hh,ww,[(r,c) for r in range(hh) for c in range(ww) if (r,c) not in holes]


def build(seed,index):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'index');r=rng(seed,f'scene:{index}')
    profile=index%4
    if profile==0:
        small=['ell','tiny'];r.shuffle(small);kinds=[small[0],'big',small[1]]
        # Put the true area winner strictly between eligible alternatives,
        # while allowing noneligible distractors anywhere in the scene.
        for k in ('hidden','open'): kinds.insert(r.randrange(len(kinds)+1),k)
    elif profile==1:
        kinds=['tie_flat','tie_square','hidden','open'];r.shuffle(kinds)
    elif profile==2:
        kinds=['double','big','open'];r.shuffle(kinds)
    else:
        kinds=['ell','big','tiny','hidden','open'];r.shuffle(kinds)
    width=r.choice((4,5));specs=[shape(k,width) for k in kinds]
    needed_h=sum(s[0] for s in specs)+len(specs)-1
    h=30 if profile==3 else r.randint(needed_h,30)
    max_width=max(s[1] for s in specs)
    wall=r.randint(max_width+1,22 if profile==3 else min(20,max_width+6))
    w=30 if profile==3 else r.randint(wall+2,min(30,wall+8))
    bg=r.choice((1,3,4,6,7,8,9));g=[[bg]*w for _ in range(h)]
    for row in g: row[wall]=5
    row=r.randint(0,h-needed_h)
    for si,(hh,ww,cells) in enumerate(specs):
        # Never already dock every object in the same scene; the stress case
        # isolates raw-contact versus post-docking eligibility.
        left=(wall-ww if profile==1 and si==0 else r.randint(0,wall-ww-1))
        for rr,cc in cells: g[row+rr][left+cc]=0
        row+=hh+1
    analyze(g)
    return g
