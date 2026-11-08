"""Three distinct rules with seed-selected, setting-independent sampler branches."""
from pathlib import Path
import importlib.util
import hashlib
HERE=Path(__file__).resolve().parent

def _load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
THRESHOLD=_load('_b286_threshold_original',HERE/'prototype.py')
ISLANDS=_load('_b286_islands_original',HERE/'islands/prototype.py')
MODES=('fixed','relative_to_largest','absorb_singletons')
def _mode(settings):
    if type(settings) is not dict or set(settings)!={'threshold_mode'} or settings['threshold_mode'] not in MODES:raise ValueError('Invalid threshold_mode')
    return settings['threshold_mode']
def branch(seed):return 'threshold' if hashlib.sha256(f'b286-mixture:{seed}'.encode()).digest()[0]%2==0 else 'islands'
def program(settings):
    mode=_mode(settings)
    return ISLANDS.program({'island_policy':'absorb'}) if mode=='absorb_singletons' else THRESHOLD.program(settings)
def solve(grid,mode):
    return ISLANDS.solve(grid,'absorb') if mode=='absorb_singletons' else THRESHOLD.mirror(grid,mode)
def _shared(seed):
    a=THRESHOLD._teaching(0,THRESHOLD._rng(seed,'shared',0))
    b=ISLANDS._mosaic([[(5,5,'x'),(5,5,'dot'),(5,5,'notch1')],[(3,4,'plain'),(3,5,'notch2'),(3,4,'domino')],[(5,5,'plain'),(3,9,'notch1')],[(3,17,'plain')]],ISLANDS._rng(seed,'shared',1,0))
    return [a,b]
def generate(seed,settings,demos=3,queries=4):
    mode=_mode(settings)
    for name,val,lo,hi in [('seed',seed,0,2**63-1),('demos',demos,2,6),('queries',queries,1,4)]:
        if type(val) is not int or not lo<=val<=hi:raise ValueError(name)
    # Materialize a stable maximum-size private lesson before taking requested prefixes.
    original=(THRESHOLD.generate(seed,{'threshold_mode':'fixed'},6,4) if branch(seed)=='threshold' else ISLANDS.generate(seed,{'island_policy':'keep'},6,4))
    inputs={'train':_shared(seed)+[p['input'] for p in original['train'][2:]],'test':[p['input'] for p in original['test']]}
    keys=[repr(g) for seq in inputs.values() for g in seq]
    if len(set(keys))!=len(keys):raise ValueError('Duplicate input in combined lesson')
    return {'train':[{'input':g,'output':solve(g,mode)} for g in inputs['train'][:demos]],'test':[{'input':g,'output':solve(g,mode)} for g in inputs['test'][:queries]],'program_solution':program(settings)}
