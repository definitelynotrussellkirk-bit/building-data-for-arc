"""Shape equivalence, edge docking, and post-docking connected-group selection.

Only adjacent native resources are read. Python labels are independent claims;
protected Racket execution is required before any owner acceptance.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
PARAMETERS = {'dock_policy': ['all_shapes', 'largest_docked_group']}
DEFAULT = {'dock_policy': 'all_shapes'}
RIVALS = ('all_shapes', 'size_match', 'bbox_match', 'translation_only',
          'rotations_only', 'largest_original', 'largest_color', 'largest_class',
          'smallest_group', 'first_group', 'last_group', 'skip_docking')


def _setting(settings):
    if (type(settings) is not dict or set(settings) != set(PARAMETERS)
            or settings.get('dock_policy') not in PARAMETERS['dock_policy']):
        raise ValueError('settings must name exactly one declared dock_policy')
    return settings['dock_policy']


def program(settings):
    policy = _setting(settings)
    text = (HERE / 'canonical.rkt').read_text()
    return text if policy == 'all_shapes' else text.replace(
        '(define output-policy "all_shapes")', f'(define output-policy "{policy}")', 1)


def rival_programs():
    text = program(DEFAULT)
    return {k: text.replace('(define output-policy "all_shapes")',
                           f'(define output-policy "{k}")', 1) for k in RIVALS}


def _grid(g):
    if (type(g) is not list or not 1 <= len(g) <= 30 or type(g[0]) is not list
            or not 1 <= len(g[0]) <= 30
            or any(type(row) is not list or len(row) != len(g[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in g)):
        raise ValueError('expected rectangular exact-integer color grid, dimensions 1..30')
    return tuple(map(tuple, g))


def _normal(cells):
    r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
    return tuple(sorted((r-r0, c-c0) for r, c in cells))


def transforms(cells, reflected=True):
    ans = []
    for flip in range(2 if reflected else 1):
        p = [(r, -c if flip else c) for r, c in cells]
        for _ in range(4):
            ans.append(_normal(p))
            p = [(c, -r) for r, c in p]
    return tuple(ans)


def _components(g, bg, connectivity=4, monochrome=False):
    remain = {(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v != bg}
    groups = []
    steps = [(-1,0),(0,-1),(0,1),(1,0)]
    if connectivity == 8: steps += [(-1,-1),(-1,1),(1,-1),(1,1)]
    while remain:
        seed = min(remain); remain.remove(seed); todo = [seed]; group = []
        while todo:
            r,c = todo.pop(); group.append((r,c))
            for dr,dc in steps:
                p = r+dr,c+dc
                if p in remain and (not monochrome or g[p[0]][p[1]] == g[r][c]):
                    remain.remove(p); todo.append(p)
        groups.append(tuple(sorted(group)))
    return tuple(groups)


def _same(a,b,policy):
    if policy == 'size_match': return len(a['cells']) == len(b['cells'])
    if policy == 'bbox_match': return sorted(a['shape_size']) == sorted(b['shape_size'])
    if policy == 'translation_only': return a['normalized'] == b['normalized']
    if policy == 'rotations_only': return a['normalized'] in transforms(b['cells'], False)
    return a['signature'] == b['signature']


@lru_cache(maxsize=2048)
def _analyze(g, policy='largest_docked_group'):
    h,w = len(g), len(g[0])
    # The admitted grammar has a unique modal background.
    bg = min(Counter(sum((list(row) for row in g), [])).items(), key=lambda x:(-x[1],x[0]))[0]
    objects = []
    for cells in _components(g,bg,8,True):
        normal = _normal(cells)
        objects.append({'cells':cells,'color':g[cells[0][0]][cells[0][1]],
                        'normalized':normal,'signature':min(transforms(cells)),
                        'shape_size':(max(r for r,c in normal)+1,max(c for r,c in normal)+1)})
    docked = [[bg]*w for _ in range(h)]
    for i,o in enumerate(objects):
        o['matched'] = any(i != j and _same(o,q,policy) for j,q in enumerate(objects))
        r0 = min(r for r,c in o['cells']); shift = (0 if o['matched'] else h-o['shape_size'][0])-r0
        o['destination'] = tuple((r+shift,c) for r,c in o['cells'])
        for r,c in o['destination']: docked[r][c] = o['color']
    return {'background':bg,'objects':objects,'docked':docked,
            'groups':_components(docked,bg,4,False)}


def analyze(g):
    return deepcopy(_analyze(_grid(g)))


def predict(g, policy='all_shapes'):
    if policy not in RIVALS+('largest_docked_group',): raise ValueError('unknown policy')
    state = _analyze(_grid(g),policy); out = deepcopy(state['docked'])
    if policy == 'all_shapes': return out
    groups,objects,bg = state['groups'],state['objects'],state['background']
    if not groups: return out
    if policy == 'largest_original': selected = max(objects,key=lambda o:len(o['cells']))['destination']
    elif policy == 'largest_color':
        counts=Counter(v for row in out for v in row if v != bg)
        color=min(counts,key=lambda c:(-counts[c],c)); selected=[(r,c) for r,row in enumerate(out) for c,v in enumerate(row) if v==color]
    elif policy == 'largest_class':
        best=max(objects,key=lambda o:sum(len(q['cells']) for q in objects if _same(o,q,policy)))
        selected=[p for q in objects if _same(best,q,policy) for p in q['destination']]
    elif policy == 'first_group': selected=groups[0]
    elif policy == 'last_group': selected=groups[-1]
    elif policy == 'smallest_group': selected=min(groups,key=len)
    elif policy == 'skip_docking':
        out=deepcopy(g); selected=max(_components(g,bg),key=len)
    else: selected=max(groups,key=len)
    for r,c in selected: out[r][c]=8
    return out


def _scene(seed,index,attempt=0):
    rng=random.Random(f'62593bfd:geometry:v1:{seed}:{index}:{attempt}')
    large=index==9
    k,m = (3,3) if index==0 else (5,2) if index==1 else (rng.choice([3,4,5]),rng.randint(3,5))
    if large: k,m=4,5
    # T and V deliberately have equal areas and equal boxes but different shapes.
    t=((0,0),(0,1),(0,2),(1,0),(2,0),(2,1))
    v=((0,0),(0,1),(0,2),(1,1),(2,1),(2,2))
    uarea = 8 if k*m==9 else rng.randint(max(7,k+1), min(12,k*m-1))
    if uarea==8:
        u=tuple((r,c) for r in range(3) for c in range(3) if (r,c)!=(1,1))
    else:
        uw=3 if uarea<=9 else 4
        u=tuple((j//uw,j%uw) for j in range(uarea))
    uw=max(c for r,c in u)+1
    width=2*m+1+9+1+uw
    W=30 if large else rng.randint(width,min(30,width+3))
    H=30 if large else rng.randint(18,28)
    bg=rng.choice([0,1,5,6,9]); palette=[c for c in range(10) if c not in (bg,8)]
    rng.shuffle(palette); g=[[bg]*W for _ in range(H)]
    shift=rng.randint(0,W-width)
    shapes=[]
    for j in range(m):
        # Mirrored hooks require reflection matching; common top bars join later.
        leg=0 if j%2==0 else 1
        shape=((0,0),(0,1))+tuple((r,leg) for r in range(1,k-1))
        shapes.append((shape,shift+2*j,palette[j%2],j%2))
    pos=shift+2*m+1
    shapes += [(t,pos,palette[2],0),(v,pos+3,palette[3],1),
               (tuple((r,2-c) for r,c in t),pos+6,palette[2],0),
               (u,pos+10,palette[0],1)]
    for j,(shape,c0,color,level) in enumerate(shapes):
        sh=max(r for r,c in shape)+1
        r0=(0 if large and j==0 else rng.randint(0,2)) if level==0 else (H-sh if large and j==1 else H-sh-rng.randint(0,2))
        for r,c in shape:g[r+r0][c+c0]=color
    # Reflecting the whole scene changes presentation, not the vertical rule.
    if rng.randrange(2):g=[row[::-1] for row in g]
    if rng.randrange(2):g=g[::-1]
    state=_analyze(_grid(g));sizes=[len(x) for x in state['groups']]
    if len(state['objects'])!=m+4 or sizes.count(max(sizes))!=1 or max(sizes)!=k*m:
        raise ValueError('construction violated object separation or unique joined winner')
    return g


@lru_cache(maxsize=128)
def _bank(seed):
    bank=[];seen=set();survivors=set(RIVALS)-{'all_shapes'}
    for index in range(10):
        for attempt in range(120):
            g=_scene(seed,index,attempt);key=_grid(g)
            if key in seen:continue
            rejected={r for r in survivors if predict(g,r)!=predict(g,'largest_docked_group')}
            if index==1 and survivors-rejected:continue
            seen.add(key);bank.append(g)
            if index<2:survivors-=rejected
            break
        else:raise ValueError(f'no distinguishing unique scene at slot {index}; survivors={sorted(survivors)}')
    if survivors:raise ValueError(f'two-demo survivors: {sorted(survivors)}')
    return tuple(bank)


def generate(seed,settings,demos=3,queries=4):
    policy=_setting(settings)
    if (type(seed) is not int or type(demos) is not int or not 2<=demos<=6
            or type(queries) is not int or not 1<=queries<=4):
        raise ValueError('integer seed, demos 2..6 and queries 1..4 required')
    bank=_bank(seed);perm=list(range(4));random.Random(f'62593bfd:presentation:{seed}').shuffle(perm)
    def pair(i):
        g=deepcopy(bank[i]);return {'input':g,'output':predict(g,policy)}
    return {'train':[pair(i) for i in range(demos)],'test':[pair(6+i) for i in perm[:queries]],
            'program_solution':program(settings),'private':{'seed':seed,'settings':deepcopy(settings),'query_permutation':perm}}


def public_turn(episode,index=0):
    if type(index) is not int or not 0<=index<len(episode['test']):raise ValueError('query index out of range')
    return {'train':[{'input':deepcopy(p['input']),'output':deepcopy(p['output'])} for p in episode['train']],
            'test':[{'input':deepcopy(episode['test'][index]['input'])}]}
