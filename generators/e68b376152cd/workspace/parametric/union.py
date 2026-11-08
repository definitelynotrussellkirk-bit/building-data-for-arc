"""Retained rules over matched inputs from both reviewed sampler banks.

Private episode rules are alternatives, never a Cartesian composition. Queries
use one seed-selected bank per episode. Diagnostic demos cover both source banks.
"""
from pathlib import Path
import importlib.util, hashlib, sys, random
from copy import deepcopy
from functools import lru_cache
HERE=Path(__file__).resolve().parent

def _load(name):
    path=HERE/name
    identity='_retained_'+hashlib.sha256(str(path).encode()).hexdigest()
    spec=importlib.util.spec_from_file_location(identity,path)
    module=importlib.util.module_from_spec(spec);sys.modules[identity]=module
    spec.loader.exec_module(module)
    return module
OLD=_load('prototype.py')
NEW=_load("incoming_bank.py")
KEY='order_policy'
VALUES=['spatial', 'largest_first']

def _mode(settings):
    if type(settings)is not dict or set(settings)!={KEY}:raise ValueError('one declared setting required')
    value=settings[KEY]
    if not any(type(value)is type(v) and value==v for v in VALUES):raise ValueError('undeclared setting')
    return value

def _rng(seed,role):
    return random.Random(int.from_bytes(hashlib.sha256(f'{HERE.parent.parent.name}:{seed}:{role}'.encode()).digest(),'big'))

def program(settings):return OLD.program({KEY:_mode(settings)})
def predict(grid,mode):return OLD.predict(grid,mode)
def _raw(seed):
    a=OLD.generate(seed,{KEY:'spatial'},6,4)
    b=NEW.generate(seed,{'object_order':'left_to_right'},6,4)
    train=[p for pair in zip(a['train'][:3],b['train'][:3]) for p in pair]
    return train,(a,b)[_rng(seed,'query-bank').randrange(2)]['test']

@lru_cache(maxsize=32)
def _bank(seed):
    train,test=_raw(seed)
    train=[p['input'] for p in train];test=[p['input'] for p in test]
    _rng(seed,'private-query-order').shuffle(test)
    if len({repr(g) for g in train+test})!=10:raise RuntimeError('duplicate episode inputs')
    for mode in VALUES:
        labels=[predict(g,mode) for g in train[:2]]
        if [v for v in VALUES if [predict(g,v) for g in train[:2]]==labels]!=[mode]:
            raise RuntimeError('two demos fail finite rule identification')
    return train,test

def generate(seed,settings,demos=3,queries=4):
    mode=_mode(settings)
    for value,low,high in [(seed,0,2**63-1),(demos,2,6),(queries,1,4)]:
        if type(value)is not int or not low<=value<=high:raise ValueError('invalid exact integer request')
    train,test=_bank(seed)
    def pairs(grids):return [{'input':deepcopy(g),'output':predict(g,mode)} for g in grids]
    return {'train':pairs(train[:demos]),'test':pairs(test[:queries]),'program_solution':program(settings)}

def public_view(episode,index):
    if type(index)is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
    return deepcopy({'train':episode['train'],'test':[{'input':episode['test'][index]['input']}]})
