"""First-marker canopy and input-derived parity-lane relay family."""
from __future__ import annotations
from functools import lru_cache
import hashlib
import importlib.util
from pathlib import Path
import random

HOME=Path(__file__).resolve().parent
COLORS=(1,2,3,5,6,7,8,9)
MODES=('first','parity_relay')
CORE_ATTEMPTS=64


def _mode(settings):
    if type(settings) is not dict or set(settings)!={'seed_mode'}:
        raise ValueError('settings must contain exactly seed_mode')
    value=settings['seed_mode']
    if type(value) is not str or value not in MODES:
        raise ValueError('seed_mode must be first or parity_relay')
    return value


def _validate(grid):
    if type(grid) is not list or not 1<=len(grid)<=30:
        raise ValueError('height must be 1..30')
    if type(grid[0]) is not list or not 1<=len(grid[0])<=30:
        raise ValueError('width must be 1..30')
    width=len(grid[0])
    if any(type(row) is not list or len(row)!=width or
           any(type(v) is not int or v not in (0,*COLORS) for v in row) for row in grid):
        raise ValueError('expected rectangular exact-integer 0/1/2/3/5/6/7/8/9 grid')
    if not any(v for row in grid for v in row):
        raise ValueError('canonical first-marker rule requires at least one marker')
    return len(grid),width


def render(height,width,cell):
    row,col,color=cell
    out=[[4 if r<=row and c%2==col%2 else 0 for c in range(width)]
         for r in range(height)]
    if row+1<height:out[row+1][col]=color
    return out


def analyze(grid,settings):
    mode=_mode(settings);h,w=_validate(grid)
    cells=[[r,c,v] for r,row in enumerate(grid) for c,v in enumerate(row) if v]
    origin=cells[0];r0,c0,_=origin
    lanes=[[4 if r>r0 and c%2==c0%2 else 0 for c in range(w)] for r in range(h)]
    eligible=[p for p in cells if lanes[p[0]][p[1]]==4]
    target=eligible[0] if mode=='parity_relay' and eligible else origin
    return {'origin':origin[:],'lane_mask':lanes,'eligible':[p[:] for p in eligible],
            'target':target[:],'output':render(h,w,target)}


def mirror(grid,settings):
    return analyze(grid,settings)['output']


def program(settings):
    mode=_mode(settings)
    return (HOME/('canonical.rkt' if mode=='first' else 'parity_relay.rkt')).read_text()


def _rng(seed,stream):
    raw=hashlib.sha256(f'033db13a9d37/native-v1/{seed}/{stream}'.encode()).digest()
    return random.Random(int.from_bytes(raw,'big'))


def _key(g):return tuple(tuple(row) for row in g)


def _grid(h,w,cells,colors):
    out=[[0]*w for _ in range(h)]
    for i,(r,c) in enumerate(cells):out[r][c]=colors[i%len(colors)]
    return out


def _active_core(rng,phase):
    # Row-major origin differs from leftmost, brightest and last markers.
    r=2+phase;c=7+phase
    points=[(r,c),(r,c+2),(r+1,phase),(r+2,3+phase),
            (r+2,11+phase),(r+3,c),(r+4,1+phase),(11,13+phase),
            (r+1,14-phase),(10,phase)]
    colors=list(COLORS);rng.shuffle(colors)
    colors[3]=rng.choice((2,3,5,6,7,8))
    colors[0]=rng.choice(tuple(v for v in (2,3,5,6,7,8) if v!=colors[3]))
    colors[4]=1;colors[6]=9
    return _grid(12,16,points,colors)


def _fallback_core(rng,phase):
    # Same-row parity matches are excluded; all strictly lower markers miss.
    r=4+phase;c=5+phase
    points=[(r,c),(r,c+2),(r+1,phase),(8,10+phase),(8,2+phase)]
    colors=list(COLORS);rng.shuffle(colors)
    return _grid(9,13,points,colors)


def _bottom_core(rng,phase):
    origin=(1,3+phase);color=rng.choice(COLORS)
    points=[origin,(1,5+phase),(2,phase),(4,10+phase),(6,7+phase),(6,11+phase)]
    colors=[color,rng.choice(COLORS),rng.choice(COLORS),rng.choice(COLORS),color,color]
    return _grid(7,13,points,colors)


@lru_cache(maxsize=1)
def _teaching_bank():
    spec=importlib.util.spec_from_file_location('seed_native_cover',HOME/'rivals.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return {mode:module.bank(mode) for mode in MODES}


def _core(seed):
    rng=_rng(seed,'core');bank=_teaching_bank()
    for attempt in range(CORE_ATTEMPTS):
        phase=rng.randrange(2)
        grids=[_active_core(rng,phase),_fallback_core(rng,1-phase),_bottom_core(rng,phase)]
        if all(any(predict(g)!=mirror(g,{'seed_mode':mode}) for g in grids)
               for mode,rivals in bank.items() for predict in rivals.values()):
            return grids,attempt
    raise RuntimeError('three-demo finite rival cover exhausted its declared 64-candidate bound')


def _draw(h,w,rng,kind=None):
    kind=kind or rng.choice(('active','active','fallback','bottom_hit'))
    r0=rng.randrange(max(1,h//3));c0=rng.randrange(w)
    origin=(r0,c0);phase=c0%2
    columns=[c for c in range(w) if c%2==phase]
    target=None
    if kind!='fallback':
        target=(h-1 if kind=='bottom_hit' else rng.randrange(r0+1,h),rng.choice(columns))
    def allowed(r,c):
        if (r,c)<=origin:return False
        if r==r0:return True
        if c%2!=phase:return True
        return target is not None and (r,c)>=target
    out=[[0]*w for _ in range(h)];out[r0][c0]=rng.choice(COLORS)
    density=rng.uniform(.32,.60) if h>=20 else rng.uniform(.10,.35)
    for r in range(r0,h):
        for c in range(w):
            if allowed(r,c) and rng.random()<density:out[r][c]=rng.choice(COLORS)
    if target:out[target[0]][target[1]]=rng.choice(COLORS)
    # Spread distractors across both halves without changing selected-hit order.
    opposite=[c for c in range(w) if c%2!=phase]
    if h>=20 and opposite:
        for r in (max(r0+1,h//3),h-1):
            for c in (opposite[0],opposite[-1]):out[r][c]=rng.choice(COLORS)
    return out


@lru_cache(maxsize=64)
def _inputs(seed):
    core,attempt=_core(seed);seen={_key(g) for g in core}
    def novel(h,w,stream):
        rng=_rng(seed,stream)
        for _ in range(64):
            g=_draw(h,w,rng);k=_key(g)
            if k not in seen:seen.add(k);return k
        raise RuntimeError('bounded distinct-input construction exhausted')
    extras=[novel(h,w,f'demo-{i}') for i,(h,w) in enumerate(((7,9),(15,19),(19,23)))]
    tests=[novel(h,w,f'query-{i}') for i,(h,w) in enumerate(((5,7),(13,17),(23,27),(30,30)))]
    _rng(seed,'query-order').shuffle(tests)
    return tuple(_key(g) for g in core)+tuple(extras),tuple(tests),attempt


def generate(seed,settings,demos=3,queries=4):
    _mode(settings)
    if type(seed) is not int or not 0<=seed<2**63:
        raise ValueError('seed must be an exact integer in 0..2**63-1')
    if type(demos) is not int or not 3<=demos<=6:
        raise ValueError('demos must be an exact integer in 3..6')
    if type(queries) is not int or not 1<=queries<=4:
        raise ValueError('queries must be an exact integer in 1..4')
    train,test,_=_inputs(seed)
    def pair(k):
        g=[list(row) for row in k]
        return {'input':g,'output':mirror(g,settings)}
    return {'train':[pair(k) for k in train[:demos]],'test':[pair(k) for k in test[:queries]],
            'program_solution':program(settings)}
