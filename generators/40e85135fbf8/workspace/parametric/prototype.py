"""Literal header equality followed optionally by largest-component selection."""
from __future__ import annotations
from functools import lru_cache
import hashlib
import importlib.util
from pathlib import Path
import random

HOME=Path(__file__).resolve().parent
MODES=('all_matches','largest_blocks')
FOUR=((-1,0),(0,-1),(0,1),(1,0))
CORE_ATTEMPTS=64


def _mode(settings):
    if type(settings) is not dict or set(settings)!={'selection_mode'}:
        raise ValueError('settings must contain exactly selection_mode')
    mode=settings['selection_mode']
    if type(mode) is not str or mode not in MODES:
        raise ValueError('selection_mode must be all_matches or largest_blocks')
    return mode


def _rectangular(grid,lo,hi):
    if type(grid) is not list or not lo<=len(grid)<=hi:
        raise ValueError(f'height must be {lo}..{hi}')
    if type(grid[0]) is not list or not lo<=len(grid[0])<=hi:
        raise ValueError(f'width must be {lo}..{hi}')
    w=len(grid[0])
    if any(type(row) is not list or len(row)!=w or
           any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid):
        raise ValueError('expected rectangular exact-integer ARC grid')
    return len(grid),w


def validate(grid):
    h,w=_rectangular(grid,2,30)
    if grid[0][0]!=0 or any(v==0 for v in grid[0][1:]) or any(row[0]==0 for row in grid[1:]):
        raise ValueError('expected zero corner and nonzero row/column headers')
    if any(grid[r][c]!=0 for r in range(1,h) for c in range(1,w)):
        raise ValueError('input interior must be zero')
    return h,w


def first_stage(grid):
    validate(grid)
    rows=[row[0] for row in grid[1:]];cols=grid[0][1:]
    return [[left if left==top else 0 for top in cols] for left in rows]


def _components(matrix):
    h,w=len(matrix),len(matrix[0]);unseen={(r,c) for r in range(h) for c in range(w) if matrix[r][c]}
    result=[]
    while unseen:
        start=min(unseen);unseen.remove(start);cells=[start];color=matrix[start[0]][start[1]]
        for r,c in cells:
            for dr,dc in FOUR:
                p=(r+dr,c+dc)
                if p in unseen and matrix[p[0]][p[1]]==color:
                    unseen.remove(p);cells.append(p)
        result.append({'color':color,'area':len(cells),'cells':[list(p) for p in sorted(cells)],
                       'box':[min(r for r,c in cells),min(c for r,c in cells),max(r for r,c in cells),max(c for r,c in cells)]})
    return result


def second_stage(matrix):
    h,w=_rectangular(matrix,1,29);parts=_components(matrix)
    biggest=max((p['area'] for p in parts),default=0)
    out=[[0]*w for _ in range(h)]
    for p in parts:
        if p['area']==biggest:
            for r,c in p['cells']:out[r][c]=p['color']
    return out


def analyze(grid,settings):
    mode=_mode(settings);matrix=first_stage(grid);parts=_components(matrix)
    biggest=max((p['area'] for p in parts),default=0)
    kept=[i for i,p in enumerate(parts) if mode=='all_matches' or p['area']==biggest]
    output=[row[:] for row in matrix] if mode=='all_matches' else second_stage(matrix)
    return {'row_headers':[row[0] for row in grid[1:]],'column_headers':grid[0][1:],
            'match_matrix':matrix,'components':parts,'max_area':biggest,
            'kept_component_indices':kept,'output':output}


def mirror(grid,settings):return analyze(grid,settings)['output']


def program(settings):
    mode=_mode(settings)
    return (HOME/('canonical.rkt' if mode=='all_matches' else 'largest_blocks.rkt')).read_text()


def _rng(seed,stream):
    raw=hashlib.sha256(f'40e85135fbf8/native-v1/{seed}/{stream}'.encode()).digest()
    return random.Random(int.from_bytes(raw,'big'))


def from_headers(rows,cols):return [[0,*cols]]+[[v,*([0]*len(cols))] for v in rows]


def _expand(runs):return [color for color,count in runs for _ in range(count)]


def _roles(rng):
    colors=sorted(rng.sample(range(1,10),5));slot=rng.randrange(4)
    private=colors[slot:slot+2]
    if rng.getrandbits(1):private.reverse()
    shared=[v for v in colors if v not in private];rng.shuffle(shared)
    return (*shared,*private)


def _transform(rows,cols,rng):
    rows=rows[:];cols=cols[:]
    if rng.getrandbits(1):rows.reverse()
    if rng.getrandbits(1):cols.reverse()
    if rng.getrandbits(1):rows,cols=cols,rows
    return from_headers(rows,cols)


def _unique_core(rng):
    a,b,c,r,k=_roles(rng)
    rows=_expand([(a,2),(r,5),(b,3),(c,1),(b,3),(c,1),(a,1),(r,1),(b,1)])
    cols=_expand([(a,7),(k,5),(b,4),(c,1),(b,2),(c,1),(a,1),(k,1),(b,1)])
    return _transform(rows,cols,rng)


def _tie_core(rng):
    a,b,c,r,k=_roles(rng)
    rows=_expand([(a,2),(b,3),(c,5),(r,5),(a,2)])
    cols=_expand([(a,3),(k,5),(b,2),(c,1),(k,1),(a,3)])
    return _transform(rows,cols,rng)


def _unit_core(rng):
    a,b,c,r,k=_roles(rng)
    return _transform([r,b,c,a,b,r,c,a],[k,a,c,b,a,k,c,b],rng)


@lru_cache(maxsize=1)
def _bank():
    s=importlib.util.spec_from_file_location('matrix_native_cover',HOME/'rivals.py')
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    return {mode:m.bank(mode) for mode in MODES}


def _core(seed):
    rng=_rng(seed,'core');bank=_bank()
    for attempt in range(CORE_ATTEMPTS):
        grids=[_unique_core(rng),_tie_core(rng),_unit_core(rng)]
        labels={mode:[mirror(g,{'selection_mode':mode}) for g in grids] for mode in MODES}
        if all(any(predict(g)!=out for g,out in zip(grids,labels[mode]))
               for mode,rivals in bank.items() for predict in rivals.values()):
            return grids,attempt
    raise RuntimeError('three-demo finite rival cover exhausted its 64-candidate bound')


def _runs(length,colors,rng):
    if len(colors)==1:return [colors[0]]*length
    values=[]
    while len(values)<length:
        choices=[v for v in colors if not values or v!=values[-1]]
        color=rng.choice(choices);run=rng.randint(1,min(6,length-len(values)))
        values.extend([color]*run)
    return values


def _edge_headers(length,a,b,c,private,rng):
    lo=max(2,length//5);hi=max(lo+1,length//3+1)
    left=rng.randrange(lo,hi);right=rng.randrange(lo,hi)
    middle=[b,c,private]
    middle+=_runs(length-left-right-len(middle),(b,c,private),rng)
    if rng.randrange(4)==0:rng.shuffle(middle)
    return [a]*left+middle+[a]*right


def _draw(h,w,rng):
    if h>=20:
        a,b,c,r,k=_roles(rng)
        rows=_edge_headers(h-1,a,b,c,r,rng);cols=_edge_headers(w-1,a,b,c,k,rng)
        # Axis reversals preserve the requested rectangular dimensions.
        if rng.getrandbits(1):rows.reverse()
        if rng.getrandbits(1):cols.reverse()
        return from_headers(rows,cols)
    palette=rng.sample(range(1,10),rng.randint(2,7))
    profile=rng.randrange(6)
    if profile==0:
        return from_headers([palette[0]]*(h-1),[palette[0]]*(w-1))
    if profile==1:
        split=max(1,len(palette)//2)
        return from_headers(_runs(h-1,palette[:split],rng),_runs(w-1,palette[split:],rng))
    row_colors=palette[:rng.randint(1,len(palette))]
    col_colors=palette[rng.randrange(len(palette)):]
    return from_headers(_runs(h-1,row_colors,rng),_runs(w-1,col_colors,rng))


def _key(g):return tuple(tuple(row) for row in g)


@lru_cache(maxsize=64)
def _inputs(seed):
    cores,attempt=_core(seed);seen={_key(g) for g in cores}
    def novel(h,w,stream):
        rng=_rng(seed,stream)
        for _ in range(64):
            g=_draw(h,w,rng);key=_key(g)
            if key not in seen:seen.add(key);return key
        raise RuntimeError('bounded distinct-input construction exhausted')
    extras=[novel(h,w,f'demo-{i}') for i,(h,w) in enumerate(((7,9),(11,15),(17,23)))]
    queries=[novel(h,w,f'query-{i}') for i,(h,w) in enumerate(((5,7),(13,17),(23,27),(30,30)))]
    _rng(seed,'query-order').shuffle(queries)
    return tuple(_key(g) for g in cores)+tuple(extras),tuple(queries),attempt


def generate(seed,settings,demos=3,queries=4):
    _mode(settings)
    if type(seed) is not int or not 0<=seed<2**63:
        raise ValueError('seed must be an exact integer in 0..2**63-1')
    if type(demos) is not int or not 3<=demos<=6:
        raise ValueError('demos must be an exact integer in 3..6')
    if type(queries) is not int or not 1<=queries<=4:
        raise ValueError('queries must be an exact integer in 1..4')
    train,test,_=_inputs(seed)
    def pair(key):
        g=[list(row) for row in key]
        return {'input':g,'output':mirror(g,settings)}
    return {'train':[pair(g) for g in train[:demos]],'test':[pair(g) for g in test[:queries]],
            'program_solution':program(settings)}
