"""Native matched-input parametric adapter for public task 97d7923e."""
from __future__ import annotations
from copy import deepcopy
import hashlib, importlib.util, json, random, sys
from pathlib import Path

BASE=Path(__file__).resolve().parent

def _load_sampler():
    path=BASE/'sampler.py'
    name='_p97_sampler_'+hashlib.sha256(str(path).encode()).hexdigest()
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec); assert spec.loader is not None
    sys.modules[name]=mod; spec.loader.exec_module(mod); return mod

SAMPLER=_load_sampler()
SETTINGS=({'rank_order':'outer_to_inner'},{'rank_order':'inner_to_outer'})
FILES={'outer_to_inner':'canonical.rkt','inner_to_outer':'inner_to_outer.rkt'}

def _integer(value,low,high,name):
    if type(value) is not int or not low<=value<=high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value

def _settings(settings):
    if type(settings) is not dict or set(settings)!={'rank_order'}:
        raise ValueError('settings must contain exactly rank_order')
    value=settings['rank_order']
    if value not in FILES: raise ValueError('unsupported rank_order')
    return value

def _rng(seed,label):
    raw=hashlib.sha256(f'97d7923e-adapter/{seed}/{label}'.encode()).digest()
    return random.Random(int.from_bytes(raw,'big'))

def program(settings):
    return (BASE/FILES[_settings(settings)]).read_text()

def analyze(grid,settings):
    return SAMPLER.analyze(grid,_settings(settings))

def mirror(grid,settings):
    return SAMPLER.solve(grid,_settings(settings))

def generate(seed,settings,demos,queries):
    _integer(seed,0,2**63-1,'seed'); _integer(demos,2,6,'demos'); _integer(queries,1,4,'queries')
    order=_settings(settings)
    demo_bank,query_bank=SAMPLER.lesson_inputs(seed)
    permutation=list(range(4)); _rng(seed,'complete-query-order').shuffle(permutation)
    ordered=[query_bank[i] for i in permutation]
    def pair(grid):
        inp=deepcopy(grid); return {'input':inp,'output':SAMPLER.solve(inp,order)}
    train=[pair(g) for g in demo_bank[:demos]]
    test=[pair(g) for g in ordered[:queries]]
    return {'train':train,'test':test,'program_solution':program(settings),
            'private':{'settings':{'rank_order':order},'query_permutation':permutation,
                       'source_query_count':4,'seed':seed}}

def public_views(episode,presentation_seed,count):
    _integer(presentation_seed,0,2**63-1,'presentation_seed')
    _integer(count,1,len(episode['test']),'count')
    order=list(range(len(episode['test']))); _rng(presentation_seed,'public-order').shuffle(order)
    order=order[:count]
    train=[{'input':deepcopy(p['input']),'output':deepcopy(p['output'])} for p in episode['train']]
    return [{'train':deepcopy(train),'test':[{'input':deepcopy(episode['test'][i]['input'])}]} for i in order]
