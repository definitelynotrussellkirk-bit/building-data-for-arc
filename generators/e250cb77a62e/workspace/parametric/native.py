"""Stamp the source stencil, then optionally recolor its largest joined region.

This opt-in grammar extends the approved sampler to 30x30, more anchors and
controlled touching/one-cell-overlapping stamps; the exact canonical program
already defines these labels. The production generator is unchanged.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
from pathlib import Path
import random

TASK_ID='e250cb77a62e'
HERE=Path(__file__).resolve().parent
PARAMETER='stamp_policy'
VALUES=('all_stamps','largest_joined')


def setting(settings: dict) -> str:
    if type(settings) is not dict or set(settings)!={PARAMETER}:
        raise ValueError(f'settings must contain exactly {PARAMETER}')
    value=settings[PARAMETER]
    if type(value) is not str or value not in VALUES:
        raise ValueError(f'{PARAMETER} must be one of {VALUES}')
    return value


def program(settings: dict) -> str:
    value=setting(settings)
    return (HERE/'rules'/('canonical.rkt' if value=='all_stamps' else 'largest_joined.rkt')).read_text()


def components(cells: set[tuple[int,int]], diagonal: bool=False) -> list[set]:
    remaining=set(cells); result=[]
    steps=[(dr,dc) for dr in (-1,0,1) for dc in (-1,0,1)
           if (dr or dc) and (diagonal or abs(dr)+abs(dc)==1)]
    while remaining:
        start=min(remaining); remaining.remove(start)
        found={start}; stack=[start]
        while stack:
            r,c=stack.pop()
            for dr,dc in steps:
                p=(r+dr,c+dc)
                if p in remaining:
                    remaining.remove(p);found.add(p);stack.append(p)
        result.append(found)
    return result


def scene(g: list[list[int]]) -> dict:
    blue=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==1]
    if not blue: raise ValueError('missing blue source frame')
    r0,c0=min(r for r,c in blue),min(c for r,c in blue)
    r1,c1=max(r for r,c in blue),max(c for r,c in blue)
    pattern={(r-r0-1,c-c0-1) for r,row in enumerate(g) for c,v in enumerate(row)
             if v==4 and r0<r<r1 and c0<c<c1}
    anchors=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==7]
    stamped={(r+dr,c+dc) for r,c in anchors for dr,dc in pattern}
    return {'frame':(r0,c0,r1,c1),'pattern':pattern,'anchors':anchors,'stamped':stamped}


def intermediate(g: list[list[int]]) -> dict:
    data=scene(g); parts=components(data['stamped'])
    if not parts: raise ValueError('no stamped component')
    ranked=sorted(parts,key=lambda s:(-len(s),min(s)))
    return {'pattern':sorted(data['pattern']),'anchors':data['anchors'],
            'component_sizes':[len(p) for p in parts],
            'largest_cells':sorted(ranked[0]),'frame':list(data['frame'])}


def validate_input(g: list[list[int]]) -> list[str]:
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list
        or not 1<=len(g[0])<=30 or any(type(row) is not list or len(row)!=len(g[0])
        or any(type(v) is not int or v not in (0,1,4,7) for v in row) for row in g)):
        return ['expected rectangular integer grid of colors 0,1,4,7 within 30x30']
    try: data=scene(g)
    except ValueError as exc: return [str(exc)]
    r0,c0,r1,c1=data['frame']; ph,pw=r1-r0-1,c1-c0-1
    expected={(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)
              if r in (r0,r1) or c in (c0,c1)}
    blue={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==1}
    if expected!=blue: return ['blue cells are not one complete hollow frame']
    pattern=data['pattern']
    if not pattern or (0,0) not in pattern or (ph-1,pw-1) not in pattern or len(components(pattern))!=1:
        return ['prototype must be connected and span both diagonal corners']
    if sum(v==4 for row in g for v in row)!=len(pattern): return ['yellow outside source frame']
    if not data['anchors']: return ['no anchors']
    if any(not (0<=r<len(g) and 0<=c<len(g[0])) for r,c in data['stamped']): return ['stamp out of bounds']
    if any(r0<=r<=r1 and c0<=c<=c1 for r,c in data['stamped']): return ['stamp overlaps source frame']
    sizes=sorted(map(len,components(data['stamped'])),reverse=True)
    if len(sizes)>1 and sizes[0]==sizes[1]: return ['largest stamped region is tied']
    return []


def apply(g: list[list[int]], value: str) -> list[list[int]]:
    setting({PARAMETER:value})
    return predict(g,value)


def _bbox_area(s: set) -> int:
    return (max(r for r,c in s)-min(r for r,c in s)+1)*(max(c for r,c in s)-min(c for r,c in s)+1)


def predict(g: list[list[int]], hypothesis: str) -> list[list[int]]:
    data=scene(g); stamped=data['stamped']; out=deepcopy(g)
    for r,c in stamped: out[r][c]=8
    if hypothesis=='all_stamps': return out
    parts=components(stamped,diagonal=hypothesis=='eight_connected')
    if hypothesis=='all_green': chosen=stamped
    elif hypothesis=='two_copies': chosen=set().union(*(s for s in parts if len(s)==2*len(data['pattern'])))
    elif hypothesis=='smallest': chosen=min(parts,key=lambda s:(len(s),min(s)))
    elif hypothesis=='first': chosen=min(parts,key=min)
    elif hypothesis=='last': chosen=max(parts,key=min)
    elif hypothesis=='bbox_area': chosen=min(parts,key=lambda s:(-_bbox_area(s),min(s)))
    elif hypothesis=='box_joined':
        r0,c0,r1,c1=data['frame'];ph,pw=r1-r0-1,c1-c0-1
        boxes={(r+dr,c+dc) for r,c in data['anchors'] for dr in range(ph) for dc in range(pw)}
        proxy=min(components(boxes),key=lambda s:(-len(s),min(s)))
        chosen=proxy & stamped
    elif hypothesis in ('largest_joined','eight_connected'):
        chosen=min(parts,key=lambda s:(-len(s),min(s)))
    else: raise ValueError(f'unknown hypothesis {hypothesis}')
    for r,c in chosen: out[r][c]=3
    return out


def materialize(hypothesis: str) -> str:
    base=(HERE/'rules/canonical.rkt').read_text()
    if hypothesis=='all_stamps': return base
    position='(+ (* 100 (first (obj-bbox o))) (second (obj-bbox o)))'
    score=f'(+ (* -10000 (obj-size o)) {position})'
    objects='(objects out 0)'
    extra=''
    paint='(obj-cells chosen)'
    if hypothesis=='two_copies':
        return base.replace('(paint-cells g targets 8)', '''(let* ((out (paint-cells g targets 8))
          (parts (filter (lambda (o) (and (= (obj-color o) 8) (= (obj-size o) (* 2 (length pattern))))) (objects out 0))))
          (paint-cells out (flatmap obj-cells parts) 3))''')
    if hypothesis=='eight_connected': objects='(objects-8 out 0)'
    elif hypothesis=='smallest': score=f'(+ (* 10000 (obj-size o)) {position})'
    elif hypothesis=='first': score=position
    elif hypothesis=='last': score=f'(* -1 {position})'
    elif hypothesis=='bbox_area':
        area='(* (+ 1 (- (third (obj-bbox o)) (first (obj-bbox o)))) (+ 1 (- (fourth (obj-bbox o)) (second (obj-bbox o)))))'
        score=f'(+ (* -10000 {area}) {position})'
    elif hypothesis=='box_joined':
        extra='''(proxy-targets
          (flatmap (lambda (seed)
            (positions-in-rect (fst seed) (snd seed)
              (+ (fst seed) (- r1 r0 2)) (+ (snd seed) (- c1 c0 2))))
            (find-color g 7)))
          (proxy (paint-cells (grid-from-fn (rows g) (cols g) (lambda (r c) 0)) proxy-targets 8))'''
        objects='(objects proxy 0)'
        paint='(filter (lambda (p) (= (cell-at out (fst p) (snd p)) 8)) (obj-cells chosen))'
    elif hypothesis=='all_green':
        return base.replace('(paint-cells g targets 8)','(let ((out (paint-cells g targets 8))) (paint-cells out (find-color out 8) 3))')
    elif hypothesis!='largest_joined': raise ValueError(hypothesis)
    replacement=f'''(let* ((out (paint-cells g targets 8))
      {extra}
      (parts (filter (lambda (o) (= (obj-color o) 8)) {objects}))
      (chosen (first (sort-by parts (lambda (o) {score})))))
      (paint-cells out {paint} 3))'''
    if base.count('(paint-cells g targets 8)')!=1: raise ValueError('canonical splice anchor drift')
    return base.replace('(paint-cells g targets 8)',replacement)


def hypotheses() -> dict[str,str]:
    names=('all_stamps','largest_joined','all_green','smallest','first','last','eight_connected','box_joined','bbox_area','two_copies')
    return {name:program({PARAMETER:name}) if name in VALUES else materialize(name) for name in names}


def teaching_findings(episode: dict,value: str) -> list[str]:
    return [name for name in hypotheses() if name!=value
            and all(predict(p['input'],name)==p['output'] for p in episode['train'])
            and any(predict(p['input'],name)!=p['output'] for p in episode['test'])]


def _draw(seed: int,slot: int) -> list[list[int]]:
    # Two mandatory demos cover reversal of component ordering, shared pixels,
    # diagonal-only contacts and larger bounding-box distractors. Every remaining
    # slot is a fresh geometry; no rejection sampling or query-based teaching.
    specs=((3,3,2),(4,4,3),(3,4,3),(4,3,3),(5,4,3),(3,5,3),
           (3,4,2),(4,3,4),(5,5,3),(5,5,4))
    ph,pw,m=specs[slot]
    rng=random.Random(int.from_bytes(hashlib.sha256(f'{TASK_ID}:{seed}:{slot}'.encode()).digest(),'big'))
    h=max(18,4*ph+m+4);w=max(18,(m+2)*pw)
    if slot==9: h=w=30
    elif slot!=0: h=min(30,h+rng.randrange(3));w=min(30,w+rng.randrange(3))
    pattern={(r,0) for r in range(ph-1)} | {(ph-2,c) for c in range(pw-1)} | {(ph-1,pw-2),(ph-1,pw-1)}
    candidates=[(r,c) for r in range(ph-1) for c in range(1,pw-1) if (r,c) not in pattern]
    rng.shuffle(candidates)
    for p in candidates:
        if rng.random()<0.6 and any((p[0]+dr,p[1]+dc) in pattern for dr,dc in ((0,1),(0,-1),(1,0),(-1,0))):pattern.add(p)
    winner_first=slot%2==0
    win_r=0 if winner_first else ph+2
    decoy_r=ph+m+1 if winner_first else 0
    anchors=[(win_r+j,j*pw) for j in range(m)]
    anchors += [(decoy_r,j*pw) for j in range(m+1)]
    shared_r=2*ph+m+2
    anchors += [(shared_r,0),(shared_r+ph-1,pw-1),(0,w-pw),(h-ph,2*pw)]
    if slot==9: anchors.append((h-ph,3*pw+1))
    if len(set(anchors))!=len(anchors): raise AssertionError('duplicate anchor in constructive layout')
    fr=h-ph-2-(rng.randrange(2) if slot not in (0,9) else 0);fc=w-pw-2
    g=[[0]*w for _ in range(h)]
    for r in range(fr,fr+ph+2):
        for c in range(fc,fc+pw+2):
            if r in (fr,fr+ph+1) or c in (fc,fc+pw+1):g[r][c]=1
    for r,c in pattern:g[fr+1+r][fc+1+c]=4
    for r,c in anchors:
        if g[r][c]:raise AssertionError('anchor overlaps source')
        g[r][c]=7
    if rng.randrange(2):g=[list(row) for row in zip(*g)]
    errors=validate_input(g)
    if errors:raise ValueError(f'constructive slot {slot}: {errors}')
    return g


def generate(seed: int,settings: dict,demos: int,queries: int) -> dict:
    value=setting(settings)
    if type(seed) is not int:raise TypeError('seed must be an exact integer, not bool')
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos must be an exact integer in 2..6')
    if type(queries) is not int or not 1<=queries<=4:raise ValueError('queries must be an exact integer in 1..4')
    inputs=[_draw(seed,i) for i in range(10)]
    if len({tuple(map(tuple,g)) for g in inputs})!=10:raise ValueError('duplicate input in maximal lesson')
    pairs=[{'input':g,'output':apply(g,value)} for g in inputs]
    return {'train':pairs[:demos],'test':pairs[6:6+queries],'program_solution':program(settings)}


def public_turn(episode: dict,query_index: int) -> dict:
    if type(query_index) is not int or not 0<=query_index<len(episode['test']):raise ValueError('query_index must select one existing query')
    return deepcopy({'train':[{'input':p['input'],'output':p['output']} for p in episode['train']],
                     'test':[{'input':episode['test'][query_index]['input']}]})
