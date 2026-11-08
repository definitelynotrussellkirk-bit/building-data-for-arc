"""Three disjoint rules on matched relay scenes, with varying source frequency.

Old Racket programs are retained verbatim. Relay scenes intentionally allow
preexisting target-2 cells and three passthrough colors, so the old sampler's
stricter Python grammar is not used to label this extended common domain.
"""
from pathlib import Path
import importlib.util
from copy import deepcopy

HERE = Path(__file__).resolve().parent

def _load(name):
    spec = importlib.util.spec_from_file_location('recolor_union_'+name, HERE/(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

old = _load('native')
relay = _load('family')
SETTINGS = ('all_sources', 'most_frequent_source', 'mapped_region_relay')

def _setting(settings):
    if settings is None:
        return 'all_sources'
    if type(settings) is not dict or set(settings) != {'recolor_scope'}:
        raise ValueError('settings must contain exactly recolor_scope')
    mode = settings['recolor_scope']
    if type(mode) is not str or mode not in SETTINGS:
        raise ValueError('unknown recolor_scope')
    return mode

def program(settings=None):
    mode = _setting(settings)
    if mode == 'mapped_region_relay':
        return relay.program_for(mode)
    return old.program({'recolor_scope':mode})

def facts(grid):
    relay._validate_scene(grid)
    pairs = relay._legend_pairs(grid)
    sources = [a for a,b in pairs]
    mapping = dict(pairs)
    counts = {a:sum(v==a for row in grid[3:] for v in row) for a in sources}
    winner = max(counts,key=counts.get)
    if list(counts.values()).count(counts[winner]) != 1:
        raise ValueError('source count winner must be unique')
    return {'sources':sources,'mapping':mapping,'source_counts':counts,'most_frequent_source':winner,
            'n_pairs':len(pairs),'body_nonzero':sum(v!=0 for row in grid[3:] for v in row)}

def transform(grid, mode):
    if mode not in SETTINGS:
        raise ValueError('unknown recolor_scope')
    info=facts(grid)
    if mode == 'mapped_region_relay':return relay.relay_transform(grid)
    if mode == 'all_sources':return relay.canonical_transform(grid)
    winner=info['most_frequent_source'];mapping=info['mapping']
    return [[mapping[v] if v==winner else v for v in row] for row in grid[3:]]

def _scene(seed,index,is_query):
    grid=relay._scene(seed,index,is_query=is_query)
    # Replacing existing inert filler preserves total occupancy and all
    # controller/payload geometry. The first two demos select different sources.
    winner=(1,3,5,3,1,5)[index] if not is_query else (5,1,3,5)[index]
    if winner != 1:
        counts={a:sum(v==a for row in grid[3:] for v in row) for a in (1,3,5)}
        needed=max(counts.values())+2-counts[winner]
        candidates=[(r,c) for r in range(3,len(grid)) for c,v in enumerate(grid[r]) if v==8]
        if len(candidates)<needed:raise RuntimeError('insufficient inert filler for source frequency witness')
        for r,c in candidates[:needed]:grid[r][c]=winner
    if facts(grid)['most_frequent_source']!=winner:raise RuntimeError('frequency witness changed')
    return grid

def generate(seed,settings=None,demos=3,queries=4):
    old._integer('seed',seed,0,2**63-1)
    old._integer('demos',demos,2,6)
    old._integer('queries',queries,1,4)
    mode=_setting(settings)
    train=[_scene(seed,i,False) for i in range(demos)]
    test=[_scene(seed,i,True) for i in range(queries)]
    if len({repr(g) for g in train+test})!=len(train)+len(test):raise RuntimeError('duplicate inputs')
    def pair(g):return {'input':deepcopy(g),'output':transform(g,mode)}
    return {'train':[pair(g) for g in train],'test':[pair(g) for g in test],
            'program_solution':program({'recolor_scope':mode})}


def rival_transform(grid,name):
    if name not in old.RIVALS:raise ValueError('unknown rival')
    info=facts(grid);mapping=info['mapping']
    if name=='zero_unmapped':return [[mapping.get(v,0) for v in row] for row in grid[3:]]
    selected=old._selected_for_rival(info,name)
    return [[mapping[v] if v==selected else v for v in row] for row in grid[3:]]
