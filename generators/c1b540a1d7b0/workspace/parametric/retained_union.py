"""Disjoint whole/selected-component classification and post-arm room selection."""
from pathlib import Path
import importlib.util
from copy import deepcopy
from functools import lru_cache
HERE=Path(__file__).resolve().parent

def _load(name):
    spec=importlib.util.spec_from_file_location('room_union_'+name,HERE/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
old=_load('prototype');residual=_load('residual_family')
SETTINGS=('all_components','largest_component','largest_residual_room')

def normalize_settings(settings=None):
    if settings is None:return {'component_scope':'all_components'}
    if type(settings) is dict and set(settings)=={'room_policy'}:
        mode=residual._policy(settings)
        return {'component_scope':'all_components' if mode=='all_rooms' else 'largest_residual_room'}
    if type(settings) is not dict or set(settings)!={'component_scope'} or type(settings['component_scope']) is not str or settings['component_scope'] not in SETTINGS:
        raise ValueError('settings must name one declared component_scope')
    return dict(settings)

def program(settings=None):
    mode=normalize_settings(settings)['component_scope']
    return residual.program({'room_policy':'largest_room'}) if mode=='largest_residual_room' else old.program({'component_scope':mode})

def transform(grid,settings):
    mode=normalize_settings(settings)['component_scope']
    return residual.transform(grid,'largest_room') if mode=='largest_residual_room' else old.transform(grid,{'component_scope':mode})

def _separate_small_component(raw,top):
    grid=[list(row) for row in raw];w=len(grid[0])
    strip=[[0]*w for _ in range(3)]
    strip[0 if top else 2][w//2-1:w//2+2]=[5]*3
    result=strip+grid if top else grid+strip
    old.largest_component_intermediate(result)
    return result

@lru_cache(maxsize=64)
def _inputs(seed):
    train,test=residual._inputs(seed)
    train=[_separate_small_component(raw,bool(i%2)) for i,raw in enumerate(train)]
    test=[_separate_small_component(raw,bool(i%2)) for i,raw in enumerate(test[:3])]+[[list(row) for row in test[3]]]
    # The 30x30 four-network stress remains unpadded. Require distinct gray
    # component sizes as well as the existing unique residual-room maximum.
    for attempt in range(17):
        sizes=[len(part) for part in old.components5(test[3])]
        if len(sizes)==len(set(sizes)):break
        if attempt==16:raise RuntimeError('distinct stress components exhausted bounded retries')
        test[3]=residual._stress_scene(residual._rng(seed,'union-stress-'+str(attempt)))
    old.largest_component_intermediate(test[3])
    return tuple(tuple(tuple(row) for row in g) for g in train),tuple(tuple(tuple(row) for row in g) for g in test)

def generate(seed,settings=None,demos=3,queries=4):
    old._exact_int(seed,'seed',0,2**63-1);old._exact_int(demos,'demos',2,6);old._exact_int(queries,'queries',1,4)
    settings=normalize_settings(settings);train,test=_inputs(seed)
    def pair(raw):
        g=[list(row) for row in raw]
        return {'input':deepcopy(g),'output':transform(g,settings)}
    return {'train':[pair(g) for g in train[:demos]],'test':[pair(g) for g in test[:queries]],'program_solution':program(settings)}
