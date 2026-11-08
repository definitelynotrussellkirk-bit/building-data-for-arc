"""Native three-rule family retaining both exact predecessor constructor banks."""
from pathlib import Path
from functools import lru_cache
import copy
import hashlib
import importlib.util
import sys

BASE=Path(__file__).resolve().parent
# The authoring preflight hashes Python/Racket, but not arbitrary JSON resources.
# Pin this retained configuration in hashed Python as well as promotion.resources.
CONFIG_SHA256='f9aea5ebc3f0a2feb4193b8b802ee8119202114c074ff8e3d0748ed9b2e7cad4'
if hashlib.sha256((BASE/'union-config.json').read_bytes()).hexdigest()!=CONFIG_SHA256:
    raise ValueError('retained union configuration drift')

def load(name):
    p=BASE/(name+'.py');key='_selective_'+hashlib.sha256(str(p).encode()).hexdigest()
    spec=importlib.util.spec_from_file_location(key,p)
    module=importlib.util.module_from_spec(spec);sys.modules[key]=module;spec.loader.exec_module(module)
    return module

U=load('union_bank');R=load('repair');S=load('selector_scenes')
MODES=R.MODES

def mode(settings):
    if type(settings)is not dict or set(settings)!={'rule'} or type(settings['rule'])is not str or settings['rule']not in MODES:
        raise ValueError('exactly one declared string rule is required')
    return settings['rule']

def program(settings):
    filename={'trim':'canonical.rkt','complete':'bank0-program1.rkt',
              'complete_most_damaged':'complete_most_damaged.rkt'}[mode(settings)]
    return (BASE/filename).read_text()

def checked_input(grid):
    old=U.table(grid)
    if old is None or old!=[R.solve(grid,k) for k in ('trim','complete')]:
        raise ValueError('input leaves the retained common semantic domain')
    return grid

@lru_cache(maxsize=64)
def inputs(seed):
    legacy_train,legacy_test=U.inputs(seed)
    train=[checked_input(S.scene(seed,i)) for i in range(2)]
    train.extend(copy.deepcopy(x[0]) for x in legacy_train[:4])
    stress=[]
    for bi,bank in enumerate(U.BANKS):
        for attempt in range(32):
            ep=bank.generate(seed+attempt*100003,U.CONFIG['banks'][bi]['default'],2,4)
            candidate=ep['test'][3]['input']
            if len(candidate)!=30 or len(candidate[0])!=30:continue
            try:checked_input(candidate)
            except ValueError:continue
            stress.append(candidate);break
        else:raise RuntimeError('common-domain 30x30 bank sampling exhausted')
    added=checked_input(S.scene(seed,103,query=True))
    held=[x[0] for x in legacy_test if x[0]not in train+stress+[added]]
    if not held:raise RuntimeError('legacy held-out diversity exhausted')
    test=[held[0],*stress,added]
    keys=[str(g) for g in train+test]
    if len(set(keys))!=10:raise RuntimeError('duplicate episode input')
    return train,test

def generate(seed,settings,demos=2,queries=4):
    selected=mode(settings)
    for value,lo,hi in ((seed,0,2**63-1),(demos,2,6),(queries,1,4)):
        if type(value)is not int or not lo<=value<=hi:raise ValueError('unsupported exact integer request')
    train,test=inputs(seed)
    def pairs(grids):return [dict(input=copy.deepcopy(g),output=R.solve(g,selected)) for g in grids]
    return dict(train=pairs(train[:demos]),test=pairs(test[:queries]),program_solution=program(settings))

def public_view(episode,index):
    if type(index)is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
    return {'train':[{'input':copy.deepcopy(p['input']),'output':copy.deepcopy(p['output'])} for p in episode['train']],
            'test':[{'input':copy.deepcopy(episode['test'][index]['input'])}]}
