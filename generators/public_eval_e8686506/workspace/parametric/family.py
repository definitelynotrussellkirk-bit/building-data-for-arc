"""Translation-only rectangle assembly, plus a solved-placement selector.

The modal color is background. A candidate rectangle has the total foreground
area. The uniquely densest such rectangle is the retained scaffold. Outside
same-color 8-components translate, without rotations, to exactly tile its holes.
Generated scenes admit exactly one colored tiling; interchangeable copies of
an identical same-colored tile are not treated as different answers.
"""
from __future__ import annotations
from collections import Counter, deque
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random

MODES=('assemble','first_cavity_piece')
RIVALS=('other_setting','scaffold_only','first_source_piece','largest_piece','smallest_piece',
        'last_cavity_piece','lowest_color','highest_color','solid_scaffold_color')
SELECTION={'assemble':0,'first_cavity_piece':1,'first_source_piece':2,'largest_piece':3,
           'smallest_piece':4,'last_cavity_piece':5,'lowest_color':6,'highest_color':7,
           'scaffold_only':8,'solid_scaffold_color':9}


def validate_grid(g):
    if type(g) is not list or not 1<=len(g)<=30 or any(type(row) is not list for row in g):
        raise ValueError('grid must be a nonempty list of rows, at most 30 high')
    w=len(g[0])
    if not 1<=w<=30 or any(len(row)!=w for row in g):raise ValueError('rectangular width 1..30 required')
    if any(type(v) is not int or not 0<=v<=9 for row in g for v in row):raise ValueError('exact integer colors 0..9 required')
    return tuple(tuple(row) for row in g)


def _components(g,bg):
    seen=set(); result=[]; h=len(g); w=len(g[0])
    for r in range(h):
        for c in range(w):
            if g[r][c]==bg or (r,c) in seen:continue
            color=g[r][c]; stack=[(r,c)]; seen.add((r,c)); cells=[]
            while stack:
                p=stack.pop(); cells.append(p)
                for dr in (-1,0,1):
                    for dc in (-1,0,1):
                        q=(p[0]+dr,p[1]+dc)
                        if (dr or dc) and 0<=q[0]<h and 0<=q[1]<w and q not in seen and g[q[0]][q[1]]==color:
                            seen.add(q);stack.append(q)
            result.append({'color':color,'cells':tuple(sorted(cells))})
    return result


def _frame(g,bg):
    h,w=len(g),len(g[0]); n=sum(v!=bg for row in g for v in row)
    if n==0:raise ValueError('no foreground')
    ps=[[0]*(w+1) for _ in range(h+1)]
    for r in range(h):
        for c in range(w):ps[r+1][c+1]=(g[r][c]!=bg)+ps[r][c+1]+ps[r+1][c]-ps[r][c]
    best=None; ties=0
    for hh in range(1,h+1):
        if n%hh:continue
        ww=n//hh
        if ww>w:continue
        for r in range(h-hh+1):
            for c in range(w-ww+1):
                score=ps[r+hh][c+ww]-ps[r][c+ww]-ps[r+hh][c]+ps[r][c]
                if best is None or score>best[0]:best=(score,r,c,hh,ww);ties=1
                elif score==best[0]:ties+=1
    if best is None:raise ValueError('foreground area has no rectangular factorization inside canvas')
    return best,ties


def _tile_solutions(scaffold,pieces,bg,limit):
    """Bounded exact cover; return different colored grids, not copy permutations."""
    h,w=len(scaffold),len(scaffold[0]); holes={(r,c) for r in range(h) for c in range(w) if scaffold[r][c]==bg}
    if sum(len(p['cells']) for p in pieces)!=len(holes):raise ValueError('area not conserved')
    items=[]
    for idx,p in enumerate(pieces):
        r0=min(r for r,c in p['cells']); c0=min(c for r,c in p['cells'])
        shape=tuple(sorted((r-r0,c-c0) for r,c in p['cells']))
        ph=max(r for r,c in shape)+1; pw=max(c for r,c in shape)+1
        placements=[]
        for r in range(h-ph+1):
            for c in range(w-pw+1):
                cells=frozenset((r+rr,c+cc) for rr,cc in shape)
                if cells<=holes:placements.append((r*w+c,cells))
        items.append((idx,p['color'],shape,placements))
    items.sort(key=lambda it:(-len(it[2]),it[1],it[2],it[0]))
    answers=[]; outputs=set(); nodes=0
    def search(k,remaining,placed,last):
        nonlocal nodes
        nodes+=1
        if nodes>200000:raise ValueError('bounded exact-cover search exhausted')
        if len(answers)>=limit:return
        if k==len(items):
            if remaining:return
            result=[list(row) for row in scaffold]
            for p in placed:
                for r,c in p['cells']:result[r][c]=p['color']
            key=tuple(map(tuple,result))
            if key not in outputs:
                outputs.add(key);answers.append((result,sorted(placed,key=lambda p:p['source_index'])))
            return
        idx,color,shape,placements=items[k]; signature=(color,shape)
        for offset,cells in placements:
            if cells<=remaining and offset>last.get(signature,-1):
                search(k+1,remaining-cells,placed+[{'source_index':idx,'color':color,'cells':tuple(sorted(cells))}],{**last,signature:offset})
                if len(answers)>=limit:return
    search(0,holes,[],{})
    return answers


@lru_cache(maxsize=512)
def _analyze(key):
    g=[list(row) for row in key];freq=Counter(v for row in g for v in row)
    bg=min(freq,key=lambda v:(-freq[v],v))
    (score,r0,c0,h,w),ties=_frame(g,bg)
    scaffold=[row[c0:c0+w] for row in g[r0:r0+h]]
    outside=[[bg if r0<=r<r0+h and c0<=c<c0+w else v for c,v in enumerate(row)] for r,row in enumerate(g)]
    pieces=_components(outside,bg)
    solutions=_tile_solutions(scaffold,pieces,bg,1)
    if not solutions:raise ValueError('no translation-only exact cover of scaffold')
    result,placed=solutions[0]
    holes=sorted((r,c) for r in range(h) for c in range(w) if scaffold[r][c]==bg)
    if not holes:raise ValueError('at least one cavity and external tile required')
    first=next(p for p in placed if holes[0] in p['cells'])
    last=next(p for p in placed if holes[-1] in p['cells'])
    return dict(bg=bg,frame=[r0,c0,h,w],frame_ties=ties,retained_cells=score,
                scaffold=scaffold,pieces=pieces,placed=placed,assembled=result,first=first,last=last)


def analyze(g):return deepcopy(_analyze(validate_grid(g)))


def unique_colored_tiling(g):
    info=_analyze(validate_grid(g))
    return info['frame_ties']==1 and len(_tile_solutions(info['scaffold'],info['pieces'],info['bg'],2))==1


def solve(g,mode='assemble',rival=None):
    if mode not in MODES:raise ValueError('unknown rendering mode')
    info=_analyze(validate_grid(g)); selected=mode
    if rival is not None:
        if rival not in RIVALS:raise ValueError('unknown rival')
        selected=MODES[1-MODES.index(mode)] if rival=='other_setting' else rival
    if selected=='assemble':return deepcopy(info['assembled'])
    result=deepcopy(info['scaffold']);placed=info['placed']
    if selected=='scaffold_only':return result
    if selected=='solid_scaffold_color':
        color=Counter(v for row in result for v in row if v!=info['bg']).most_common(1)[0][0]
        return [[color if v==info['bg'] else v for v in row] for row in result]
    if selected=='first_cavity_piece':p=info['first']
    elif selected=='last_cavity_piece':p=info['last']
    elif selected=='first_source_piece':p=placed[0]
    elif selected=='largest_piece':p=max(placed,key=lambda p:len(p['cells']))
    elif selected=='smallest_piece':p=min(placed,key=lambda p:len(p['cells']))
    elif selected=='lowest_color':p=min(placed,key=lambda p:p['color'])
    elif selected=='highest_color':p=max(placed,key=lambda p:p['color'])
    else:raise ValueError('unknown selector')
    for r,c in p['cells']:result[r][c]=p['color']
    return result


def local_first_candidates(g):
    """Tiles locally fitting the first cavity, before enforcing all other holes."""
    info=_analyze(validate_grid(g)); bg=info['bg']
    holes={(r,c) for r,row in enumerate(info['scaffold']) for c,v in enumerate(row) if v==bg}
    first=min(holes); candidates=set()
    for index,p in enumerate(info['pieces']):
        r0=min(r for r,c in p['cells']);c0=min(c for r,c in p['cells'])
        shape={(r-r0,c-c0) for r,c in p['cells']}
        for pr,pc in shape:
            shifted={(r+first[0]-pr,c+first[1]-pc) for r,c in shape}
            if shifted<=holes:candidates.add(index)
    return sorted(candidates)


def self_check(g):
    try:
        info=analyze(g)
        return [] if info['frame_ties']==1 and unique_colored_tiling(g) else ['non-unique frame or colored tiling']
    except (ValueError,TypeError,IndexError) as e:return [str(e)]


def _rng(seed,tag):
    return random.Random(int.from_bytes(hashlib.sha256(f'{seed}:{tag}'.encode()).digest(),'big'))

SHAPES=( ((0,0),(1,0)), ((0,0),(1,0),(1,1)),
        ((0,0),(0,1),(0,2),(1,1)), ((0,0),(1,0),(2,0),(2,1),(2,2)),
        ((0,0),(0,1),(0,2),(1,0),(1,1),(1,2)),
        ((0,0),(0,1),(0,2),(1,1),(2,0),(2,1),(2,2)) )


def _scene(seed,tag,stress=False,attempt=0):
    rng=_rng(seed,f'{tag}:{attempt}')
    H,W=(30,30) if stress else rng.choice(((18,21),(20,23),(23,24),(25,26)))
    fh,fw=(12,10) if stress else rng.choice(((8,8),(8,9),(9,8),(9,10)))
    palette=rng.sample(range(10),7);bg,sc1,sc2,*colors=palette
    # Ensure the retained frame extends to both its top and bottom borders.
    grid=[[bg]*W for _ in range(H)]
    r0,c0=(0,0) if stress else (rng.randrange(2),rng.randrange(2))
    target=[[sc1 if r<fh//2 else sc2 for c in range(fw)] for r in range(fh)]
    shapes=rng.sample(SHAPES,4)
    slots=[(0,1),(1,fw-3),(fh-3,0),(fh-3,fw-3)]
    for shape,(r,c),color in zip(shapes,slots,colors):
        for dr,dc in shape:target[r+dr][c+dc]=bg
    for r,row in enumerate(target):grid[r0+r][c0:c0+fw]=row
    # Two distant right-hand tiles and two bottom tiles; shuffle source order.
    outside=[(0,W-3),(H//2,W-3),(H-3,0),(H-3,W//2)]
    rng.shuffle(outside)
    for shape,(r,c),color in zip(shapes,outside,colors):
        for dr,dc in shape:grid[r+dr][c+dc]=color
    # Full-scene isometries preserve all piece orientations relative to holes.
    if rng.randrange(2):grid=[row[::-1] for row in grid]
    if rng.randrange(2):grid=grid[::-1]
    if rng.randrange(2):grid=[list(row) for row in zip(*grid)]
    return grid


@lru_cache(maxsize=64)
def _inputs(seed):
    demos=None
    for attempt in range(128):
        candidate=[_scene(seed,f'demo:{i}',attempt=attempt) for i in range(2)]
        if any(self_check(g) for g in candidate):continue
        if not any(len(local_first_candidates(g))>1 for g in candidate):continue
        ok=True
        for mode in MODES:
            for rival in RIVALS:
                # Rivals identical to a setting on all lawful scenes are harmless;
                # here none of the declared selectors is identical by construction.
                if all(solve(g,mode,rival=rival)==solve(g,mode) for g in candidate):ok=False;break
            if not ok:break
        if ok:demos=candidate;break
    if demos is None:raise ValueError('bounded teaching construction exhausted')
    used={validate_grid(g) for g in demos}
    def fresh(tag,stress=False):
        for attempt in range(128):
            g=_scene(seed,tag,stress,attempt)
            if validate_grid(g) not in used and not self_check(g):used.add(validate_grid(g));return g
        raise ValueError('bounded distinct scene construction exhausted')
    demos += [fresh(f'demo:{i}') for i in range(2,6)]
    queries=[fresh(f'query:{i}',i==3) for i in range(4)]
    return demos,queries


def _request(seed,settings,demos,queries):
    if type(seed) is not int or seed<0:raise ValueError('nonnegative integer seed required')
    if type(settings) is not dict or set(settings)!={'render'} or settings['render'] not in MODES:raise ValueError('exact render setting required')
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos must be 2..6')
    if type(queries) is not int or not 1<=queries<=4:raise ValueError('queries must be 1..4')
    return settings['render']


def program(settings):
    mode=_request(0,settings,2,4)
    name='canonical.rkt' if mode=='assemble' else 'first-cavity.rkt'
    return Path(__file__).with_name(name).read_text()


def generate(seed,settings,demos,queries):
    mode=_request(seed,settings,demos,queries); ds,qs=_inputs(seed)
    def pair(g):return dict(input=deepcopy(g),output=solve(g,mode))
    return dict(train=[pair(g) for g in ds[:demos]],test=[pair(g) for g in qs[:queries]],program_solution=program(settings))


def present(seed,settings,demos,queries,presentation_seed=0):
    _request(seed,settings,demos,queries)
    if type(presentation_seed) is not int:raise ValueError('integer presentation seed required')
    e=generate(seed,settings,demos,4); order=list(range(4));_rng(seed,f'presentation:{presentation_seed}').shuffle(order)
    views=[{'train':deepcopy(e['train']),'test':[{'input':deepcopy(e['test'][i]['input'])}]} for i in order[:queries]]
    return dict(public=views,private=dict(seed=seed,presentation_seed=presentation_seed,settings=deepcopy(settings),
        source_indices=order[:queries],program=e['program_solution'],source_pairs=deepcopy(e['test'])))


def rival_program(settings,rival):
    mode=_request(0,settings,2,4)
    if rival not in RIVALS:raise ValueError('unknown rival')
    selected=MODES[1-MODES.index(mode)] if rival=='other_setting' else rival
    return Path(__file__).with_name('canonical.rkt').read_text().replace('(define selection 0)',f'(define selection {SELECTION[selected]})')


def counterfactual_program(settings):return rival_program(settings,'last_cavity_piece')


def intermediate(g,settings):
    info=analyze(g)
    return {'scaffold_bbox':info['frame'],'first_cavity_tile':info['first'],'wrong_last_cavity_tile':info['last'],'locally_legal_first_tiles':local_first_candidates(g)}


def dependency():
    return dict(step_a='Infer the retained rectangle, solve the translation-only exact cover, and identify the placed tile covering its first row-major cavity cell.',
        intermediate='The selected external tile color and its complete translated cell coordinates inside the solved rectangle.',
        step_b='Paint that selected placed tile over the retained scaffold; leave every other cavity as background.',
        why_b_depends_on_a='The source position, color rank and size do not identify which tile fits the first cavity. Rendering needs the input-derived exact-cover placement; substituting the last-cavity tile changes the output.')
