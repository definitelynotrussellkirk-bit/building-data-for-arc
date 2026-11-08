"""Geometry and deterministic authoring claims for red-source stack transfers.

Racket is the label authority; these claims are independently replayed by preflight.
No source-data/gold access, catalog import, or process-global random mutations.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import hashlib
import random

MODES = ('broadcast', 'balanced')
RIVALS = ('identity', 'keep_bars', 'column_count', 'max_donor', 'pixel_count',
          'static_shortest', 'reverse_tie', 'all_to_tallest', 'other_setting')


def integer(x, lo, hi, name):
    if type(x) is not int or not lo <= x <= hi:
        raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return x


def grid(value):
    if (type(value) is not list or not 1 <= len(value) <= 30 or
        type(value[0]) is not list or not 1 <= len(value[0]) <= 30 or
        any(type(r) is not list or len(r) != len(value[0]) or
            any(type(v) is not int or not 0 <= v <= 9 for v in r) for r in value)):
        raise ValueError('Expected a rectangular 1..30 exact-integer ARC grid')
    return deepcopy(value)


def rng(seed, salt):
    return random.Random(int.from_bytes(hashlib.sha256(f'{seed}:9aaea919:{salt}'.encode()).digest(), 'big'))


def objects(g, bg):
    h,w=len(g)-1,len(g[0]); unseen={(r,c) for r in range(h) for c in range(w) if g[r][c]!=bg}
    out=[]
    while unseen:
        start=min(unseen); unseen.remove(start); stack=[start]; cells=[]; color=g[start[0]][start[1]]
        while stack:
            r,c=stack.pop(); cells.append((r,c))
            for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if q in unseen and g[q[0]][q[1]]==color:
                    unseen.remove(q); stack.append(q)
        out.append({'cells':sorted(cells),'color':color,
                    'r1':min(r for r,c in cells),'r2':max(r for r,c in cells),
                    'c1':min(c for r,c in cells),'c2':max(c for r,c in cells)})
    return out


def analyze(value):
    g=grid(value); h,w=len(g),len(g[0]); bg=Counter(v for row in g for v in row).most_common(1)[0][0]
    if bg in (2,3,5) or h<4 or any(v not in (bg,2,3) for v in g[-1]):
        raise ValueError('Expected a distinct background and bottom red/green instruction bars')
    parts=objects(g,bg); columns={}
    for p in parts: columns.setdefault((p['c1'],p['c2']),[]).append(p)
    towers=[]
    for (c1,c2),ls in sorted(columns.items()):
        ls.sort(key=lambda x:x['r1']); bottom=ls[-1]; oh=bottom['r2']-bottom['r1']+1
        gap=h-2-bottom['r2']; pitch=oh+gap
        norm=lambda p:{(r-p['r1'],c-p['c1']) for r,c in p['cells']}
        tag=set(g[-1][c1:c2+1])
        if len(tag)!=1 or gap<1 or any(p['color']!=bottom['color'] or norm(p)!=norm(bottom) for p in ls):
            raise ValueError('Each column requires identical separated motifs and one uniform bar')
        if any(b['r1']-a['r1']!=pitch for a,b in zip(ls,ls[1:])):
            raise ValueError('Repeated motifs must have the inferred common within-column pitch')
        towers.append({'parts':ls,'c1':c1,'c2':c2,'count':len(ls),'pitch':pitch,
                       'tag':next(iter(tag)), 'color':bottom['color']})
    if any(a['c2']>=b['c1'] for a,b in zip(towers,towers[1:])):
        raise ValueError('Stack horizontal spans must be disjoint')
    donors=[t for t in towers if t['tag']==2]; receivers=[t for t in towers if t['tag']==3]
    if not donors or not receivers:
        raise ValueError('A lesson needs both donor and receiver stacks')
    total=sum(t['count'] for t in donors)
    if any(t['parts'][0]['r1']-total*t['pitch']<0 for t in receivers):
        raise ValueError('Broadcast transfer must fit within the input canvas')
    return {'grid':g,'background':bg,'towers':towers,'donors':donors,'receivers':receivers,'total':total}


def solve(value, distribution='broadcast', *, strategy=None):
    if distribution not in MODES: raise ValueError('Unknown distribution')
    a=analyze(value); out=deepcopy(a['grid']); h=len(out); total=a['total']; receivers=a['receivers']
    if strategy=='column_count': total=len(a['donors'])
    if strategy=='max_donor': total=max(t['count'] for t in a['donors'])
    if strategy=='pixel_count':
        # A plausible normalized-area shortcut: assume all donor motifs share
        # the first donor's area, and keep the inferred count on the grammar.
        pixels=sum(len(p['cells']) for t in a['donors'] for p in t['parts'])
        capacity=min(t['parts'][0]['r1']//t['pitch'] for t in receivers)
        total=min(capacity, max(1,pixels//len(a['donors'][0]['parts'][0]['cells'])))
    for c,v in enumerate(out[-1]):
        if v in (2,3): out[-1][c]=a['background']
    for t in a['donors']:
        for p in t['parts']:
            for r,c in p['cells']: out[r][c]=5
    additions=[0]*len(receivers)
    if distribution=='broadcast': additions=[total]*len(receivers)
    else:
        heights=[t['count'] for t in receivers]
        for _ in range(total):
            if strategy=='static_shortest': j=min(range(len(heights)),key=lambda j:(receivers[j]['count'],j))
            elif strategy=='all_to_tallest': j=max(range(len(heights)),key=lambda j:(heights[j],-j))
            elif strategy=='reverse_tie': j=min(range(len(heights)),key=lambda j:(heights[j],-j))
            else: j=min(range(len(heights)),key=lambda j:(heights[j],j))
            heights[j]+=1; additions[j]+=1
    for t,n in zip(receivers,additions):
        for j in range(1,n+1):
            for r,c in t['parts'][0]['cells']: out[r-j*t['pitch']][c]=t['color']
    if strategy=='keep_bars': out[-1]=a['grid'][-1][:]
    return out


def rival(g, name, distribution='balanced'):
    if name=='identity': return grid(g)
    if name=='other_setting': return solve(g,MODES[1-MODES.index(distribution)])
    return solve(g,distribution,strategy=name)


def build(seed, index):
    integer(seed,0,2**63-1,'seed'); integer(index,0,2**31-1,'index')
    r=rng(seed,f'scene:{index}'); profile=index%4
    donors,receivers=[([2,1],[1,1]),([1],[2,1,2]),([3,1],[1,1]),([2,1],[1,2])][profile]
    specs=[(2,n) for n in donors]+[(3,n) for n in receivers]+[(None,r.randint(1,3))]
    r.shuffle(specs); total=sum(donors); bg=r.choice([0,1,4,6,7,8,9]); colors=[c for c in range(10) if c not in (bg,5)]
    stress=profile==3
    widths=[r.choice([3,4]) for _ in specs]; gap=r.choice([1,2]); margin=1
    needed_w=sum(widths)+len(specs)-1+2*margin; w=30 if stress else needed_w+r.randint(0,30-needed_w)
    shapes=[]; required_h=0
    donor_seen=0
    for (tag,n),ow in zip(specs,widths):
        oh=r.choice([1,2,3]); kind=r.randrange(3)
        if profile==0 and tag==2:
            # Deliberately separate unit counts from pixel area at two demos.
            oh=3 if donor_seen==0 else 1
            kind=0; donor_seen+=1
        if kind==0 or oh==1: cells=[(a,b) for a in range(oh) for b in range(ow)]
        elif kind==1: cells=[(a,b) for a in range(oh) for b in range(ow) if a==oh-1 or b==0]
        else: cells=[(a,b) for a in range(oh) for b in range(ow) if a in (0,oh-1) or b in (0,ow-1)]
        final=n+(total if tag==3 else 0)
        # bottom bar row + lower gap, then final stacked motif extent
        required_h=max(required_h,1+gap+final*oh+(final-1)*gap)
        shapes.append((oh,cells))
    if required_h>30:  # legal profile uses at most five motifs, each <=3 high
        raise ValueError('Construction exceeds the lawful output size')
    h=30 if stress else r.randint(max(8,required_h),30)
    g=[[bg]*w for _ in range(h)]
    left=0 if stress else r.randint(0,w-needed_w)
    c=left+margin
    for (tag,n),ow,(oh,cells) in zip(specs,widths,shapes):
        color=r.choice(colors); pitch=oh+gap; bottom=h-2-gap
        for j in range(n):
            top=bottom-oh+1-j*pitch
            for a,b in cells: g[top+a][c+b]=color
        if tag:
            for b in range(ow): g[-1][c+b]=tag
        c+=ow+1
    analyze(g)
    return g
