"""Whole-component endpoint caps, optionally followed by residual selection.

Production sampler/authority are untouched. The separate native grammar includes
multiple straight objects, cycles, diagonal contacts, degenerate lengths and
large canvases; the selected canonical Racket expression is total on this domain.
"""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

HOME=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('base_142_'+hashlib.sha256(str(HOME).encode()).hexdigest(), HOME.parents[1]/'generator.py')
gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
MODES=('caps','residual_largest')
POLICIES=MODES+('identity','horizontal_only','vertical_only','maximal_runs','all_colors',
    'ignore_singletons','ignore_pairs','ignore_length3','caps_twice',
    'horizontal_then_relay','vertical_then_relay','runs_then_relay',
    'original_largest','skip_caps_relay','all_remaining','first_remaining',
    'last_remaining','smallest_remaining','bbox_remaining','eight_remaining',
    'straight_remaining','nonstraight_remaining','tie_last','allcolor_remaining')


def validate_grid(g):
    if type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30:
        raise ValueError('grid must be a rectangular 1..30 list')
    if any(type(row) is not list or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g):
        raise ValueError('grid must contain exact integer colors 0..9')


def components(g,color,diagonal=False):
    remain={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==color}
    ds=[(dr,dc) for dr in (-1,0,1) for dc in (-1,0,1) if (dr or dc) and (diagonal or abs(dr)+abs(dc)==1)]
    groups=[]
    while remain:
        start=min(remain);remain.remove(start);todo=[start];part={start}
        while todo:
            r,c=todo.pop()
            for dr,dc in ds:
                p=(r+dr,c+dc)
                if p in remain:remain.remove(p);todo.append(p);part.add(p)
        groups.append(sorted(part))
    return groups


def straight(g):
    return len({r for r,c in g})==1 or len({c for r,c in g})==1


def largest(groups,*,last=False,bbox=False):
    if not groups:return []
    def score(g):
        return ((max(r for r,c in g)-min(r for r,c in g)+1)*(max(c for r,c in g)-min(c for r,c in g)+1)) if bbox else len(g)
    return min(groups,key=lambda g:(-score(g),tuple(-v for v in g[0]) if last else g[0]))


def caps(g,policy='caps'):
    if policy=='caps':return gen.rule_mirror(g)
    if policy=='maximal_runs':
        out=copy.deepcopy(g);h,w=len(g),len(g[0])
        for transpose in (False,True):
            for r in range(w if transpose else h):
                line=[g[c][r] if transpose else g[r][c] for c in range(h if transpose else w)]
                c=0
                while c<len(line):
                    if line[c]!=2:c+=1;continue
                    end=c
                    while end+1<len(line) and line[end+1]==2:end+=1
                    if end>c:
                        for x in (c,end):
                            if transpose:out[x][r]=4
                            else:out[r][x]=4
                    c=end+1
        return out
    out=copy.deepcopy(g)
    colors=sorted({v for row in g for v in row if v}) if policy=='all_colors' else [2]
    for color in colors:
        for cells in components(g,color):
            rs={r for r,c in cells};cs={c for r,c in cells}
            if not straight(cells):continue
            if policy=='horizontal_only' and len(rs)!=1:continue
            if policy=='vertical_only' and len(cs)!=1:continue
            if policy=='ignore_singletons' and len(cells)==1:continue
            if policy=='ignore_pairs' and len(cells)==2:continue
            if policy=='ignore_length3' and len(cells)==3:continue
            for r,c in (cells[0],cells[-1]):out[r][c]=4
    return out


def intermediate(g):
    validate_grid(g)
    selected=largest(components(caps(g),2))
    return {'size':len(selected),'cells':[list(p) for p in selected]}


def solve(g,policy):
    validate_grid(g)
    if policy not in POLICIES:raise ValueError('unknown policy')
    if policy=='identity':return copy.deepcopy(g)
    if policy in ('caps','horizontal_only','vertical_only','maximal_runs','all_colors','ignore_singletons','ignore_pairs','ignore_length3'):
        return caps(g,policy)
    if policy=='caps_twice':return caps(caps(g))
    basis={'horizontal_then_relay':'horizontal_only','vertical_then_relay':'vertical_only','runs_then_relay':'maximal_runs'}.get(policy,'caps')
    out=caps(g,basis)
    parts=components(out,2)
    if policy in ('original_largest','skip_caps_relay'):parts=components(g,2)
    if policy=='skip_caps_relay':out=copy.deepcopy(g)
    if policy=='eight_remaining':parts=components(out,2,True)
    if policy=='straight_remaining':parts=[p for p in parts if straight(p)]
    if policy=='nonstraight_remaining':parts=[p for p in parts if not straight(p)]
    if policy=='allcolor_remaining':
        parts=[]
        for color in sorted({v for row in out for v in row if v}):parts.extend(components(out,color))
    selected=largest(parts,last=policy=='tie_last',bbox=policy=='bbox_remaining')
    if policy=='all_remaining':selected=[p for part in parts for p in part]
    elif policy=='first_remaining':selected=parts[0] if parts else []
    elif policy=='last_remaining':selected=parts[-1] if parts else []
    elif policy=='smallest_remaining':selected=min(parts,key=lambda p:(len(p),p[0])) if parts else []
    for r,c in selected:
        if out[r][c]==2:out[r][c]=8
    return out


def _rng(seed,role,index):
    return random.Random(int.from_bytes(hashlib.sha256(f'142-native-v1:{seed}:{role}:{index}'.encode()).digest(),'big'))


def _scene(seed,role,index,h,w):
    rng=_rng(seed,role,index);k=rng.choice((2,3,4));size=2*k+1;profile=index%3
    g=[[0]*w for _ in range(h)]
    def paint(cells,color=2):
        for r,c in cells:
            if not(0<=r<h and 0<=c<w) or g[r][c]!=0:raise RuntimeError('constructive placement collision')
            g[r][c]=color
    if profile==0:hlen,vlen,hrow=size+1,rng.randint(3,size-1),0
    elif profile==1:hlen,vlen,hrow=size+3,size+4,2
    else:hlen,vlen,hrow=size+2,size+1,0
    paint([(hrow,c) for c in range(1,hlen+1)])
    paint([(r,w-1) for r in range(vlen)])
    # Same-size T and L: the T starts earlier, but the L has the larger box.
    paint([(5,c) for c in range(1,k+3)]+[(r,1+(k+2)//2) for r in range(6,5+k)])
    lc=w//2+1
    ell=[(r,0) for r in range(k+1)]+[(k,c) for c in range(1,k+1)]
    for _ in range(rng.randrange(4)):
        ell=[(c,k-r) for r,c in ell]
    paint([(6+r,lc+c) for r,c in ell])
    # A cycle diagonal to, not 4-connected to, the T.
    paint([(r,c) for r in (6,7) for c in (k+3,k+4)])
    # Degenerate lengths and a length-three branch are explicitly taught.
    paint([(h-1,1)]);paint([(h-1,5),(h-1,6)])
    paint([(h-5,c) for c in (1,2,3)])
    color=rng.choice((1,3,5,6,7,9))
    paint([(h-3,c) for c in range(1,6)],rng.choice((1,3,5,6,7,9)))
    # Alternate decoy dominance: a permanently largest non-red object would
    # make an erroneous all-color relay indistinguishable from plain caps.
    dh,dw = (2,3) if profile==1 else (4,5)
    paint([(r,c) for r in range(h-6,h-6+dh) for c in range(w-8,w-8+dw)],color)
    # Lawful spatial diversity; first two lessons keep the T before the L.
    if rng.randrange(2):g=[row[::-1] for row in g]
    if role!='demo' or index>=2:
        if rng.randrange(2):g=g[::-1]
        if rng.randrange(2):g=[list(row) for row in zip(*g)]
    return g


def _stress(seed):
    rng=_rng(seed,'stress',0);g=[[0]*30 for _ in range(30)]
    for c in range(26):g[0][c]=2
    for r in range(26):g[r][29]=2
    for r in range(3,26):g[r][0]=2
    for c in range(18):g[29][c]=2
    for r in range(4,25,5):
        for c in range(4,25,5):
            color=rng.choice((2,2,3,5,6,7,9))
            # Both cyclic blocks and bent objects, not an enlarged padded motif.
            coords=[(r+dr,c+dc) for dr in range(3) for dc in range(3)]
            if rng.randrange(2):coords=coords[:6]+[(r+2,c)]
            for rr,cc in coords:g[rr][cc]=color
    return g


def input_bank(seed):
    train=[]
    for i in range(6):
        rng=_rng(seed,'dimensions',i)
        train.append(_scene(seed,'demo',i,18+i%3+rng.randrange(4),22+i%4+rng.randrange(4)))
    queries=[_scene(seed,'query',i,*shape) for i,shape in enumerate(((18,22),(23,24),(26,27)))]+[_stress(seed)]
    keys=[json.dumps(g) for g in train+queries]
    if len(keys)!=len(set(keys)):raise RuntimeError('duplicate constructive scene')
    return train,queries


def teaching_check(e):
    survivors=[p for p in POLICIES if all(solve(x['input'],p)==x['output'] for x in e['train'])]
    bad=[p for p in survivors if any(solve(x['input'],p)!=x['output'] for x in e['test'])]
    return {'survivors':survivors,'query_disagreeing_survivors':bad,'scope':'finite Python policy class, not universal identification'}


def public_view(e,index):
    from reviewer_support import public_challenge_bytes
    if type(index) is not int or not 0<=index<len(e['test']):raise ValueError('index must select one query')
    return json.loads(public_challenge_bytes({'train':e['train'],'test':[e['test'][index]]}))
