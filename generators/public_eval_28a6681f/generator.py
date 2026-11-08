"""28a6681f: finite-volume liquid settling around fixed, multicolored barriers.

No source dataset or labels are consulted during sampling or transformation.
The Python functions are claims; reference.rkt independently executes labels.
"""
from __future__ import annotations
RULE_TASK_ID = 'ee_28a6681f'
import hashlib
import random

GENERATOR_ID = TASK_ID = 'public_eval_28a6681f'
VERSION = '1.0.0'
SUMMARY = 'Settle blue liquid through nearest downhill openings around solid barriers.'
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
AXES = {}
INVARIANTS = ['rectangular ARC grid', 'blue is liquid', 'all other nonzero colors are solid', 'closed canvas boundary']


def check_grid(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list
        or not 1<=len(g[0])<=30 or any(type(row) is not list or len(row)!=len(g[0])
        or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('expected a rectangular 1..30 grid of integer colors 0..9')


def pools(g, connectivity=4):
    seen=set(); result=[]
    for r,row in enumerate(g):
        for c,v in enumerate(row):
            if v!=1 or (r,c) in seen: continue
            todo=[(r,c)];seen.add((r,c));component=[]
            while todo:
                p=todo.pop();component.append(p)
                for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)) + (((-1,-1),(-1,1),(1,-1),(1,1)) if connectivity==8 else ()):
                    q=(p[0]+dr,p[1]+dc)
                    if 0<=q[0]<len(g) and 0<=q[1]<len(row) and g[q[0]][q[1]]==1 and q not in seen:
                        seen.add(q);todo.append(q)
            result.append(sorted(component))
    return result


def retain(g, policy='largest', connectivity=4):
    groups=pools(g, connectivity)
    if not groups:return [r[:]for r in g]
    if policy=='smallest':chosen=min(groups,key=lambda x:(len(x),x[0]))
    elif policy=='leftmost':chosen=min(groups,key=lambda x:(min(c for r,c in x),x[0]))
    elif policy=='lowest':chosen=max(groups,key=lambda x:(max(r for r,c in x),-x[0][1]))
    elif policy=='bbox':chosen=max(groups,key=lambda x:(max(r for r,c in x)-min(r for r,c in x)+1)*(max(c for r,c in x)-min(c for r,c in x)+1))
    else:chosen=max(groups,key=len)
    cells=set(chosen)
    return [[0 if v==1 and (r,c) not in cells else v for c,v in enumerate(row)]for r,row in enumerate(g)]


def settle(g, flow='nearest'):
    """Lower drops settle fully before the next drop. Bound: <= H*blue moves."""
    out=[row[:] for row in g];h,w=len(out),len(out[0])
    for sr in range(h-2,-1,-1):
        for sc in range(w):
            if out[sr][sc]!=1:continue
            r,c=sr,sc
            while r+1<h:
                lo=hi=c
                if flow!='vertical':
                    while lo>0 and out[r][lo-1] in (0,1):lo-=1
                    while hi+1<w and out[r][hi+1] in (0,1):hi+=1
                choices=[x for x in range(lo,hi+1) if out[r+1][x]==0]
                if not choices:break
                if flow=='leftmost':x=min(choices)
                elif flow=='rightmost':x=max(choices)
                else:x=min(choices,key=lambda x:(abs(x-c),-x if flow=='right_tie' else x))
                out[r][c]=0;out[r+1][x]=1;r,c=r+1,x
    return out


def solve(g, mode='settle'):
    check_grid(g)
    if mode not in ('settle','largest_pool'):raise ValueError('unknown mode')
    out=settle(g)
    return retain(out) if mode=='largest_pool' else out


def policy_outputs(g):
    full=settle(g)
    result={'identity':[row[:] for row in g], 'settle':full,
            'largest_pool':retain(full), 'select_before_settling':settle(retain(g)),
            'smallest_pool':retain(full,'smallest'), 'leftmost_pool':retain(full,'leftmost'),
            'lowest_pool':retain(full,'lowest'), 'largest_bbox':retain(full,'bbox'),
            'eight_connected_pool':retain(full,connectivity=8)}
    for flow in ('vertical','leftmost','rightmost','right_tie'):
        a=settle(g,flow);result[flow]=a;result[flow+'_largest']=retain(a)
    return result


def _rng(seed,index):
    return random.Random(int.from_bytes(hashlib.sha256(f'{TASK_ID}:{seed}:{index}'.encode()).digest(),'big'))


def sample(seed, index, *, size=None):
    rng=_rng(seed,index)
    h,w=size or (rng.randint(10,20),rng.randint(12,24))
    g=[[0]*w for _ in range(h)]
    colors=rng.sample(range(2,10),4)
    # Four basins with independently varying floor levels and saddle heights.
    divs=[0,w//4,w//2,3*w//4,w-1]
    for i,(left,right) in enumerate(zip(divs,divs[1:])):
        floor=h-1-rng.randrange(max(1,h//4))
        for r in range(floor,h):
            for c in range(left,right+1):g[r][c]=colors[i]
    for i,c in enumerate(divs):
        top=rng.randint(max(2,h//4),max(3,h//2))
        for r in range(top,h):g[r][c]=colors[i%4]
    # Occasionally add a suspended diagonal chute; it changes nearest openings.
    if index%3==1:
        start=rng.randrange(1,max(2,w//3))
        for k in range(min(h//3,w-start-2)):
            g[1+k][start+k]=colors[2]
    # A connected source block above saddles, plus independent lower trickles.
    width=rng.randint(2,max(2,w//3)); left=rng.randrange(w-width+1)
    depth=rng.randint(1,max(2,h//3))
    for r in range(depth):
        for c in range(left,left+width):
            if g[r][c]==0:g[r][c]=1
    for _ in range(rng.randint(1,w//3)):
        r=rng.randrange(max(1,h//2));c=rng.randrange(w)
        if g[r][c]==0:g[r][c]=1
    if rng.getrandbits(1):g=[row[::-1]for row in g]
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int or not 0<=seed<2**63 or type(sample_index) is not int or sample_index<0:
        raise ValueError('seed and sample_index must be nonnegative integers')
    if difficulty not in (None,'easy','medium','hard') or overrides:raise ValueError('unsupported controls')
    sizes={'easy':(10,12),'medium':(16,20),'hard':(30,30)}
    return sample(seed,sample_index,size=sizes.get(difficulty))


def self_check(g, *, difficulty=None, meta=None):
    try:check_grid(g)
    except ValueError as exc:return [str(exc)]
    if not any(1 in row for row in g):return ['scene has no liquid']
    if not any(v not in (0,1)for row in g for v in row):return ['scene has no solid']
    return []


def diagonal_reservoirs(seed):
    """A 4-vs-8 connectivity teaching scene: diagonal sealed pores vs one pool.

    Three adjacent liquid cells beat every isolated one-cell pore under 4-connectivity,
    but a chain of four diagonal pores wins under the wrong 8-connected rule.
    """
    rng=_rng(seed,9000);h,w=rng.randint(10,17),rng.randint(13,23)
    solid=rng.choice(range(2,10));g=[[0]*w for _ in range(h)]
    top=rng.randint(2,h-7);left=rng.randint(1,w-11)
    for r in range(top,top+7):
        for c in range(left,left+11):g[r][c]=solid
    for k in range(4):g[top+1+k][left+1+k]=1
    for c in range(left+7,left+10):g[top+5][c]=1
    if rng.getrandbits(1):g=[row[::-1]for row in g]
    return g
