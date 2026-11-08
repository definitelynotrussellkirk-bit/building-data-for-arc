"""Exact canonical/cue/rarest programs on shared cue-and-frequency scenes."""
from pathlib import Path
import importlib.util
from copy import deepcopy
from collections import Counter
HERE=Path(__file__).resolve().parent

def _load(name):
    spec=importlib.util.spec_from_file_location('diagonal_union_'+name,HERE/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
old=_load('native_family');rare=_load('rarest_family')
SETTINGS=('all_pairs','cue_selected_color','rarest_active_color')

def normalize_settings(settings=None):
    if settings is None:return {'completion_scope':'all_pairs'}
    if type(settings) is dict and set(settings)=={'completion'}:
        mode=rare._completion(settings)
        return {'completion_scope':'all_pairs' if mode=='all_colors' else mode}
    if type(settings) is not dict or set(settings)!={'completion_scope'} or type(settings['completion_scope']) is not str or settings['completion_scope'] not in SETTINGS:
        raise ValueError('settings must name one declared completion_scope')
    return dict(settings)

def program(settings=None):
    mode=normalize_settings(settings)['completion_scope']
    return rare.program({'completion':mode}) if mode=='rarest_active_color' else old.program({'completion_scope':mode})

def reference(grid,settings):
    mode=normalize_settings(settings)['completion_scope']
    return rare.solve(grid,mode) if mode=='rarest_active_color' else old.reference(grid,{'completion_scope':mode})

def _rarify(grid,seed,ordinal,previous):
    grid=deepcopy(grid)
    pairs=old._matching_pairs(grid)
    active=list(dict.fromkeys(p['color'] for p in pairs))
    selected=old._selected_record(grid,'nearest_pair_color')['color']
    candidates=[c for c in active if c not in (selected,active[0],active[-1],previous)]
    if not candidates:raise RuntimeError('no nonshortcut rare color candidate')
    counts=Counter(v for row in grid for v in row if v)
    candidates.sort(key=lambda c:(counts[c],(c-seed-ordinal)%9))
    chosen=candidates[0]
    target=max(3,counts[chosen])
    # Extra isolated occurrences affect frequency, never the original pair set.
    # Late-cell placement preserves first/last active color discovery.
    h,w=len(grid),len(grid[0])
    for color in [chosen]+[c for c in active if c!=chosen]:
        need=max(0,(target if color==chosen else target+1)-counts[color])
        for r in range(h-1,-1,-1):
            for c in range(w-1,-1,-1):
                if need and grid[r][c]==0 and all(not(0<=r+dr<h and 0<=c+dc<w) or grid[r+dr][c+dc]!=color for dr,dc in ((1,1),(1,-1),(-1,1),(-1,-1))):
                    grid[r][c]=color;need-=1
        if need:raise RuntimeError('insufficient safe isolated cells')
    if old._matching_pairs(grid)!=pairs:raise RuntimeError('frequency extension changed active pairs')
    if rare.analyze(grid)['rarest_active_color']!=chosen:raise RuntimeError('frequency winner changed')
    return grid,chosen

def generate(seed,settings=None,demos=3,queries=4):
    old._integer(seed,0,2**63-1,'seed');old._integer(demos,2,6,'demos');old._integer(queries,1,4,'queries')
    settings=normalize_settings(settings)
    train,test=old._plan(seed);bank=[];previous=None
    for ordinal,g in enumerate(train+test):
        g,previous=_rarify(g,seed,ordinal,previous);bank.append(g)
    def pair(g):return {'input':deepcopy(g),'output':reference(g,settings)}
    return {'train':[pair(g) for g in bank[:demos]],'test':[pair(g) for g in bank[6:6+queries]],'program_solution':program(settings)}
