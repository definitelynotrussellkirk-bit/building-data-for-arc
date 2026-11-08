"""Four exact disjoint rules on matched constructive room-network scenes.

The complete classified grid is reused by two distinct post-classification
selectors: largest surviving cyan region, or most red arm cells per component.
No Cartesian combinations are introduced. Original three-rule sources remain
in retained_union.py and their exact programs are called unchanged.
"""
from pathlib import Path
import importlib.util
from copy import deepcopy
from functools import lru_cache
HERE=Path(__file__).resolve().parent

def _load(name):
    spec=importlib.util.spec_from_file_location('room_four_'+name,HERE/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
retained=_load('retained_union');armiest=_load('armiest_family')
old=retained.old;residual=retained.residual
SETTINGS=retained.SETTINGS+('armiest_component',)

def normalize_settings(settings=None):
    if type(settings) is dict and set(settings)=={'finish_rule'}:
        mode=armiest.normalize_settings(settings)['finish_rule']
        return {'component_scope':'all_components' if mode=='classify_only' else 'armiest_component'}
    if type(settings) is dict and set(settings)=={'component_scope'} and settings['component_scope']=='armiest_component':
        return dict(settings)
    return retained.normalize_settings(settings)

def program(settings=None):
    setting=normalize_settings(settings)
    if setting['component_scope']=='armiest_component':
        return armiest.program({'finish_rule':'classify_then_highlight_armiest'})
    return retained.program(setting)

def transform(grid,settings):
    setting=normalize_settings(settings)
    if setting['component_scope']=='armiest_component':
        return armiest.finish_python(grid,{'finish_rule':'classify_then_highlight_armiest'})
    return retained.transform(grid,setting)

def _raw_tip_highlight(grid):
    stage=armiest.classify(grid);parts=armiest._components(stage)
    h,w=len(grid),len(grid[0])
    def score(cells):
        return sum(sum(0<=r+dr<h and 0<=c+dc<w and grid[r+dr][c+dc]==5
                       for dr,dc in armiest.DIRS4)==1 for r,c in cells)
    chosen=max(parts,key=score);out=deepcopy(stage)
    for r,c in chosen:
        if out[r][c]==8:out[r][c]=4
    return out

def residual_maximum(grid):
    regions=residual.components(armiest.classify(grid),8)
    return max(map(len,regions))

def fixed_residual_size(grid,size):
    """Literal equal-size shortcut: highlight every cyan region of this size."""
    stage=armiest.classify(grid);out=deepcopy(stage)
    for region in residual.components(stage,8):
        if len(region)==size:
            for r,c in region:out[r][c]=3
    return out

def fixed_residual_size_program(size):
    if type(size) is not int or size not in (3,4,6):raise ValueError('undeclared fixed-size rival')
    canonical=residual.wrap_rule(residual.CANONICAL)
    return f"""(rule! (lambda (g)
      (let* ((stage ({canonical} g))
             (regions (filter (lambda (o) (and (= (obj-color o) 8) (= (obj-size o) {size})))
                              (objects stage 0))))
        (recolor-cells stage (apply append (map obj-cells regions)) 3))))"""

def teaching_rejections(grid):
    """Finite source-local rival coverage; never uses query labels."""
    names=set();rejected=set()
    for mode in retained.SETTINGS:
        expected=transform(grid,{'component_scope':mode})
        rivals=({n:lambda g,n=n:residual.transform(g,n) for n in residual.RIVALS}
                if mode=='largest_residual_room' else
                {n:lambda g,n=n:old.shortcut_output(g,n) for n in old.SHORTCUTS})
        for name,fn in rivals.items():
            key=mode+':'+name;names.add(key)
            if fn(grid)!=expected:rejected.add(key)
    for size in (3,4,6):
        key='largest_residual_room:fixed_size_'+str(size);names.add(key)
        if fixed_residual_size(grid,size)!=transform(grid,{'component_scope':'largest_residual_room'}):rejected.add(key)
    expected=transform(grid,{'component_scope':'armiest_component'})
    rivals={n:lambda g,n=n:armiest.highlight_by(armiest.classify(g),n)
            for n in ('largest_total','smallest_total','largest_cyan','top_left','bottom_right')}
    rivals.update(raw_tips=_raw_tip_highlight,identity=lambda g:g,canonical=armiest.classify)
    for name,fn in rivals.items():
        key='armiest_component:'+name;names.add(key)
        if fn(grid)!=expected:rejected.add(key)
    return names,rejected

def _network_scene(seed,label,side,attempt):
    """First network supplies a natural unique maximum; others stay below it."""
    rng=residual._rng(seed,'four-rule:'+label+':'+str(attempt))
    tile_side=(side-2)//2
    rooms=6 if tile_side<13 else 7
    tiles=[]
    for role in range(4):
        for _ in range(128):
            tile=residual._base._build_blob(rng,tile_side,tile_side,rooms,rng.randint(2,8) if role==0 else rng.randint(6,9))
            if tile is None:continue
            sizes=residual.describe(tile)['residual_sizes']
            if sizes and ((role==0 and max(sizes)>=3 and sizes.count(max(sizes))==1)
                          or (role>0 and max(sizes)<observed_maximum)):
                if role==0:observed_maximum=max(sizes)
                tiles.append(tile);break
        else:raise RuntimeError('bounded room-network construction exhausted')
    rng.shuffle(tiles);grid=[[0]*side for _ in range(side)]
    for quadrant,tile in enumerate(tiles):
        cells=[(r,c) for r,row in enumerate(tile) for c,v in enumerate(row) if v==5]
        r0,r1=min(r for r,c in cells),max(r for r,c in cells)
        c0,c1=min(c for r,c in cells),max(c for r,c in cells)
        dr=-r0 if quadrant<2 else side-1-r1
        dc=-c0 if quadrant%2==0 else side-1-c1
        for r,c in cells:grid[r+dr][c+dc]=5
    return grid

def _valid(grid):
    parts=old.components5(grid);sizes=[len(p) for p in parts]
    if len(parts)!=4 or len(set(sizes))!=4:return False
    stage=armiest.classify(grid);classified=armiest._components(stage)
    if len(classified)!=4:return False
    scores=[sum(stage[r][c]==2 for r,c in p) for p in classified]
    if scores.count(max(scores))!=1:return False
    winner=classified[scores.index(max(scores))]
    return any(stage[r][c]==8 for r,c in winner)

@lru_cache(maxsize=64)
def _inputs(seed):
    # Search only demonstration candidates; exact pair coverage is checked
    # before queries are generated. No failed rival execution counts as evidence.
    pool=[];selected=None
    for attempt in range(32):
        side=26 if attempt%2==0 else 28
        grid=_network_scene(seed,'teaching',side,attempt)
        if not _valid(grid):continue
        names,rejects=teaching_rejections(grid)
        for prior,prior_rejects in pool:
            if residual_maximum(prior)!=residual_maximum(grid) and prior_rejects|rejects==names:
                selected=[prior,grid];break
        if selected is not None:break
        pool.append((grid,rejects))
    if selected is None:raise RuntimeError('two-demo combined teaching budget exhausted')
    bank=selected[:]
    seen={repr(g) for g in bank}
    for label,side in [('demo2',24),('demo3',27),('demo4',29),('demo5',30),
                       ('query0',24),('query1',27),('query2',29),('query3',30)]:
        for attempt in range(32):
            grid=_network_scene(seed,label,side,attempt)
            if (_valid(grid) and repr(grid) not in seen
                    and (label!='query1' or residual_maximum(grid)!=residual_maximum(bank[6]))):
                bank.append(grid);seen.add(repr(grid));break
        else:raise RuntimeError('bounded distinct valid scene construction exhausted')
    return tuple(tuple(tuple(row) for row in grid) for grid in bank)

def generate(seed,settings=None,demos=3,queries=4):
    old._exact_int(seed,'seed',0,2**63-1);old._exact_int(demos,'demos',2,6);old._exact_int(queries,'queries',1,4)
    settings=normalize_settings(settings);bank=_inputs(seed)
    def pair(raw):
        grid=[list(row) for row in raw]
        return {'input':grid,'output':transform(grid,settings)}
    return {'train':[pair(g) for g in bank[:demos]],'test':[pair(g) for g in bank[6:6+queries]],'program_solution':program(settings)}
