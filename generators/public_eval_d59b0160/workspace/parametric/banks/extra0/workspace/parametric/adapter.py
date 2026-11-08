"""Key-color containment, canonical deletion and a relational area relay.

Native resources are adjacent. Python labels are claims replayed by Racket.
The original dataset is neither loaded nor memorized by this sampler.
"""
from __future__ import annotations
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import random

HERE=Path(__file__).resolve().parent
PARAMETERS={'erase_policy':['all_matches','area_relay']}
DEFAULT={'erase_policy':'all_matches'}
RIVALS=('all_matches','smallest_area','largest_any','first_match','key_count','exact_colors','any_color','second_largest','largest_duplicate','most_colors')


def _setting(settings):
    if (type(settings) is not dict or set(settings)!=set(PARAMETERS)
        or type(settings['erase_policy']) is not str
        or settings['erase_policy'] not in PARAMETERS['erase_policy']):
        raise ValueError('settings must name exactly one declared erase_policy')
    return settings['erase_policy']


def program(settings):
    policy=_setting(settings);source=(HERE/'canonical.rkt').read_text()
    return source if policy=='all_matches' else source.replace(
        '(define output-policy "all_matches")',f'(define output-policy "{policy}")',1)


def rival_programs():
    source=program(DEFAULT)
    return {name:source.replace('(define output-policy "all_matches")',
        f'(define output-policy "{name}")',1) for name in RIVALS}


def _grid(grid):
    if (type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list
        or not 1<=len(grid[0])<=30 or any(type(row) is not list or len(row)!=len(grid[0])
        or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
        raise ValueError('expected rectangular exact-integer 1..30 color grid')
    return tuple(tuple(row) for row in grid)


def _components(grid):
    remaining={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v!=7};parts=[]
    while remaining:
        start=min(remaining);remaining.remove(start);todo=[start];cells=[start]
        while todo:
            r,c=todo.pop()
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    p=r+dr,c+dc
                    if p in remaining:
                        remaining.remove(p);todo.append(p);cells.append(p)
        parts.append(sorted(cells))
    return parts


@lru_cache(maxsize=1024)
def _analyze(grid):
    green=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==3]
    if not green:raise ValueError('missing green key')
    r1,r2=min(r for r,c in green),max(r for r,c in green)
    c1,c2=min(c for r,c in green),max(c for r,c in green)
    keys={grid[r][c] for r in range(r1,r2+1) for c in range(c1,c2+1)}-{7,3}
    if not keys or 0 in keys:raise ValueError('key needs nonblack colors on orange')
    mask=[list(row) for row in grid]
    for r in range(r1,r2+1):
        for c in range(c1,c2+1):mask[r][c]=7
    panels=[]
    for cells in _components(mask):
        colors={grid[r][c] for r,c in cells}-{0}
        shape=[max(r for r,c in cells)-min(r for r,c in cells)+1,
               max(c for r,c in cells)-min(c for r,c in cells)+1]
        panels.append({'cells':cells,'colors':sorted(colors),'shape':shape,'matched':keys<=colors})
    return {'key_colors':sorted(keys),'key_box':[r1,c1,r2,c2],'panels':panels}


def analyze(grid):return deepcopy(_analyze(_grid(grid)))


def predict(grid,policy='all_matches'):
    if policy not in RIVALS+('area_relay',):raise ValueError('unknown policy')
    info=_analyze(_grid(grid));out=deepcopy(grid);panels=info['panels']
    matches=[p for p in panels if p['matched']];survivors=[p for p in panels if not p['matched']]
    erased=matches
    if policy=='exact_colors':erased=[p for p in matches if set(p['colors'])==set(info['key_colors'])]
    if policy=='any_color':erased=[p for p in panels if set(p['colors'])&set(info['key_colors'])]
    for panel in erased:
        for r,c in panel['cells']:out[r][c]=7
    area=-1
    if matches:
        if policy=='smallest_area':area=min(len(p['cells']) for p in matches)
        elif policy=='largest_any':area=max(len(p['cells']) for p in panels)
        elif policy=='first_match':area=len(matches[0]['cells'])
        elif policy=='key_count':area=len(info['key_colors'])
        elif policy=='most_colors':area=len(max(matches,key=lambda p:len(p['colors']))['cells'])
        elif policy=='second_largest':
            ranked=sorted(survivors,key=lambda p:-len(p['cells']))
            area=len(ranked[1]['cells']) if len(ranked)>1 else -1
        elif policy=='largest_duplicate':
            sizes=[len(p['cells']) for p in panels]
            repeated=[s for s in sizes if sizes.count(s)>1]
            area=max(repeated) if repeated else -1
        elif policy=='area_relay':area=max(len(p['cells']) for p in matches)
    for panel in survivors:
        if len(panel['cells'])==area:
            for r,c in panel['cells']:out[r][c]=7
    return out


def _transform(g,k):
    if k>=4:g=[row[::-1] for row in g]
    for _ in range(k%4):g=[list(row) for row in zip(*g[::-1])]
    return g


def _scene(seed,index,attempt=0):
    rng=random.Random(f'd59b0160:geometry:1:{seed}:{index}:{attempt}')
    h,w=(30,30) if index==9 else (rng.randint(27,30),rng.randint(27,30))
    # Target and same-area receiver have different aspect ratios (not rotation).
    profiles=[((3,4),(2,6),(2,3)),((4,4),(2,8),(2,4)),((4,6),(3,8),(3,4))]
    if h==w==30:profiles += [((3,6),(2,9),(3,3)),((6,6),(4,9),(4,4))]
    target,receiver,small=profiles[-1] if index==9 else rng.choice(profiles)
    palette=[1,2,4,5,6,8,9];rng.shuffle(palette)
    count=rng.randint(2,4);keys=palette[:count];extras=palette[count:]
    g=[[7]*w for _ in range(h)]
    # Unique green L bounds the key; sparse duplicate-insensitive color examples.
    for r in range(4):g[r][3]=3
    for c in range(4):g[3][c]=3
    positions=[(r,c) for r in range(3) for c in range(3)];rng.shuffle(positions)
    for p,v in zip(positions,keys+[keys[0]]):g[p[0]][p[1]]=v
    # Roles occupy separate slots, with an orange moat. Largest unmatched plate
    # defeats original-size selection; the small and key-count receivers make
    # both rival relays visible rather than aliases of canonical deletion.
    roles=[('target',target),('small',small),('receiver',receiver),('small_receiver',small),
           ('largest',(8,8)),('key_count',(1,count)),
           ('other',(8,8) if (index%3>=1 or index==9) else (1,5)),
           ('other',(7,8) if (index%3==2 or index==9) else (1,7))]
    rng.shuffle(roles)
    for slot,(role,shape) in enumerate(roles,1):
        sr,sc=divmod(slot,3)
        rlo=sr*(h//3);rhi=(sr+1)*(h//3) if sr<2 else h
        clo=sc*(w//3);chi=(sc+1)*(w//3) if sc<2 else w
        ph,pw=shape
        # Last slots contact the bottom/right boundary on the 30x30 stress.
        r0=rhi-ph if index==9 and sr==2 else rng.randint(rlo,rhi-ph-1)
        c0=chi-pw if index==9 and sc==2 else rng.randint(clo,chi-pw-1)
        for r in range(r0,r0+ph):
            for c in range(c0,c0+pw):g[r][c]=0
        spots=[(r,c) for r in range(r0,r0+ph) for c in range(c0,c0+pw)];rng.shuffle(spots)
        if role=='target':marks=keys+([extras[0]] if index%2==0 else [keys[0]])
        elif role=='small':marks=keys+([keys[0]] if index%2==0 else [extras[0]])
        else:marks=keys[:-1]+[extras[0]]
        # Tiny key-count rectangle may have every cell colored, still a panel.
        for p,v in zip(spots,marks):g[p[0]][p[1]]=v
    g=_transform(g,rng.randrange(8))
    info=_analyze(tuple(map(tuple,g)));panels=info['panels'];matches=[p for p in panels if p['matched']]
    if len(panels)!=8 or len(matches)!=2:raise ValueError('construction merged panels or changed key containment')
    area=max(len(p['cells']) for p in matches)
    if sum(not p['matched'] and len(p['cells'])==area for p in panels)!=1:raise ValueError('relay receiver not unique')
    return g


@lru_cache(maxsize=128)
def _bank(seed):
    bank=[];seen=set();survivors=set(RIVALS)-{'all_matches'}
    for index in range(10):
        for attempt in range(80):
            g=_scene(seed,index,attempt);key=tuple(map(tuple,g))
            if key in seen:continue
            target=predict(g,'area_relay')
            rejected={name for name in survivors if predict(g,name)!=target}
            # The second lesson must break any positional first-match shortcut.
            if index==1 and survivors-rejected:continue
            bank.append(g);seen.add(key)
            if index<2:survivors-=rejected
            break
        else:raise ValueError(f'no distinguishing scene at slot {index}')
    if survivors:raise ValueError(f'two-demo survivors: {sorted(survivors)}')
    return tuple(bank)


def generate(seed,settings,demos=3,queries=4):
    policy=_setting(settings)
    if type(seed) is not int or type(demos) is not int or not 2<=demos<=6 or type(queries) is not int or not 1<=queries<=4:
        raise ValueError('integer seed, demonstrations 2..6 and queries 1..4 required')
    bank=_bank(seed);permutation=list(range(4));random.Random(f'd59b0160:presentation:{seed}').shuffle(permutation)
    def pair(i):
        g=deepcopy(bank[i]);return {'input':g,'output':predict(g,policy)}
    return {'train':[pair(i) for i in range(demos)],'test':[pair(6+i) for i in permutation[:queries]],
        'program_solution':program(settings),'private':{'seed':seed,'settings':deepcopy(settings),'query_permutation':permutation}}


def public_turn(episode,index=0):
    if type(index) is not int or not 0<=index<len(episode['test']):raise ValueError('query index out of range')
    return {'train':[{'input':deepcopy(p['input']),'output':deepcopy(p['output'])} for p in episode['train']],
        'test':[{'input':deepcopy(episode['test'][index]['input'])}]}
