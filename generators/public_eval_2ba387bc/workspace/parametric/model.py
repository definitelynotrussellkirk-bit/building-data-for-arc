"""Classify square frames/solids, order each class, then pack exact blocks."""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import hashlib
import random

MODES=('row','column')
RIVALS=('alternate_axis','reverse_order','color_ascending','color_descending','swap_classes','truncate_shorter','solidify','serial_packing','six_block_budget')

def validate_grid(g):
    if type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30:
        raise ValueError('expected nonempty grid up to 30x30')
    if any(type(row) is not list or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g):
        raise ValueError('exact integer rectangular color grid required')

def infer(g):
    validate_grid(g);counts=Counter(v for row in g for v in row);ranked=counts.most_common()
    if len(ranked)<2 or ranked[0][1]==ranked[1][1]:raise ValueError('background must be uniquely modal')
    bg=ranked[0][0];todo={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v!=bg};blocks=[]
    while todo:
        start=min(todo);color=g[start[0]][start[1]];todo.remove(start);cells={start};stack=[start]
        while stack:
            r,c=stack.pop()
            for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                p=r+dr,c+dc
                if p in todo and g[p[0]][p[1]]==color:
                    todo.remove(p);cells.add(p);stack.append(p)
        r0=min(r for r,c in cells);r1=max(r for r,c in cells);c0=min(c for r,c in cells);c1=max(c for r,c in cells)
        size=r1-r0+1
        if size!=c1-c0+1 or size<3:raise ValueError('blocks must be squares of side at least three')
        rect={(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)}
        frame={p for p in rect if p[0] in (r0,r1) or p[1] in (c0,c1)}
        if cells==rect:kind='solid'
        elif cells==frame and all(g[r][c]==bg for r,c in rect-frame):kind='frame'
        else:raise ValueError('expected a full square or exact one-cell hollow frame')
        blocks.append(dict(row=r0,column=c0,color=color,size=size,kind=kind,
                           patch=[row[c0:c1+1] for row in g[r0:r1+1]]))
    if len({b['size'] for b in blocks})!=1:raise ValueError('all block sizes must agree')
    if {b['kind'] for b in blocks}!={'solid','frame'}:raise ValueError('both classes must occur')
    return dict(background=bg,blocks=blocks,size=blocks[0]['size'])

def ordered_buckets(state,mode,rival=None):
    if mode not in MODES:raise ValueError('order_axis must be row or column')
    effective=('column' if mode=='row' else 'row') if rival=='alternate_axis' else mode
    key=(lambda b:(b['row'],b['column'])) if effective=='row' else (lambda b:(b['column'],b['row']))
    if rival in ('color_ascending','color_descending'):
        key=lambda b:(b['color'],b['row'],b['column'])
    reverse=rival in ('reverse_order','color_descending')
    if rival=='serial_packing':
        allblocks=sorted(state['blocks'],key=key)
        return [allblocks[::2],allblocks[1::2]]
    frames=sorted((b for b in state['blocks'] if b['kind']=='frame'),key=key,reverse=reverse)
    solids=sorted((b for b in state['blocks'] if b['kind']=='solid'),key=key,reverse=reverse)
    return [solids,frames] if rival=='swap_classes' else [frames,solids]

def render(state,buckets,rival=None):
    s=state['size'];n=(min if rival=='truncate_shorter' else max)(map(len,buckets))
    if not 1<=n*s<=30 or 2*s>30:raise ValueError('packed result exceeds ARC dimensions')
    out=[[state['background']]*(2*s) for _ in range(n*s)]
    for slot,bucket in enumerate(buckets):
        for i,b in enumerate(bucket[:n]):
            patch=[[b['color']]*s for _ in range(s)] if rival=='solidify' else b['patch']
            for r,row in enumerate(patch):out[i*s+r][slot*s:(slot+1)*s]=row[:]
    return out

def solve(g,mode='row',rival=None):
    state=infer(g)
    if rival=='six_block_budget':state['blocks']=state['blocks'][:6]
    return render(state,ordered_buckets(state,mode,rival),rival)

def rng_for(seed,tag):
    if type(seed) is not int:raise ValueError('seed must be an exact integer')
    return random.Random(int.from_bytes(hashlib.sha256(f'2ba387bc/v1/{seed}/{tag}'.encode()).digest(),'big'))

def _scene(rng,h,w,s,nf,ns,stress):
    bg=rng.randrange(10);colors=rng.sample([c for c in range(10) if c!=bg],nf+ns)
    if stress:
        rr=cc=[0,12,25]
    else:
        rr=[rng.randint(0,1),h//2-s//2+rng.randint(-1,1),h-s-rng.randint(0,1)]
        cc=[rng.randint(0,1),w//2-s//2+rng.randint(-1,1),w-s-rng.randint(0,1)]
    slots=[(r,c) for r in rr for c in cc];rng.shuffle(slots)
    kinds=['frame']*nf+['solid']*ns;rng.shuffle(kinds)
    g=[[bg]*w for _ in range(h)]
    for (r0,c0),color,kind in zip(slots,colors,kinds):
        for r in range(s):
            for c in range(s):
                if kind=='solid' or r in (0,s-1) or c in (0,s-1):g[r0+r][c0+c]=color
    return g

def sample_input(seed,index,*,query=False):
    if type(index) is not int or index<0 or type(query) is not bool:raise ValueError('invalid scene index or query flag')
    rng=rng_for(seed,f'{"query" if query else "demo"}/{index}')
    profiles=([(18,21,3,3,3),(22,25,4,4,2),(27,26,5,3,4),(30,30,5,3,6)] if query else
              [(20,23,4,4,2),(24,23,3,3,6),(18,24,3,3,3),(25,26,5,3,2),(27,25,4,4,3),(26,28,3,2,5)])
    h,w,s,nf,ns=profiles[index%len(profiles)];stress=query and index%4==3
    for _ in range(96):
        g=_scene(rng,h,w,s,nf,ns,stress)
        try:
            state=infer(g)
            if not query and index%6 in (0,1):
                # These two small lessons refute competitors from demonstrations
                # alone; no query data or hidden selected setting is consulted.
                if any(solve(g,mode,name)==solve(g,mode) for mode in MODES for name in RIVALS if name!='six_block_budget' or index%6==1):continue
            if stress and sum(v!=state['background'] for row in g for v in row)<190:continue
            return g
        except ValueError:
            continue
    raise RuntimeError('bounded input construction exhausted')

def query_order(seed):
    order=list(range(4));rng_for(seed,'presentation').shuffle(order);return order
