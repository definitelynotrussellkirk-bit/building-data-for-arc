"""Bounded native interface. All resources are exact adjacent paths."""
from pathlib import Path
import importlib.util
import hashlib
import sys

BASE=Path(__file__).resolve().parent
_path=BASE/'sampler.py'
_name='_placement_sampler_'+hashlib.sha256(str(_path).encode()).hexdigest()[:16]
_spec=importlib.util.spec_from_file_location(_name,_path)
sampler=importlib.util.module_from_spec(_spec);sys.modules[_name]=sampler
_spec.loader.exec_module(sampler)

def _mode(settings):
    if type(settings) is not dict or set(settings)!={'overlap_priority'} or settings['overlap_priority'] not in ('source_order','largest_first'):
        raise ValueError('settings must declare only overlap_priority=source_order|largest_first')
    return settings['overlap_priority']

def program(settings):
    return (BASE/('canonical.rkt' if _mode(settings)=='source_order' else 'largest_first.rkt')).read_text()

def predict(grid, settings):
    return sampler.predict(grid,_mode(settings))

def generate(seed,settings,demos,queries):
    mode=_mode(settings)
    if type(seed) is not int or not 0<=seed<2**63:raise ValueError('invalid seed')
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos must be 2..6')
    if type(queries) is not int or queries!=4:raise ValueError('exactly four queries are required')
    draw, _ = sampler.teaching_seed(seed)
    def pair(index):
        grid=sampler.sample(seed if index>=100 else draw,index)
        return {'input':grid,'output':sampler.predict(grid,mode)}
    return {'train':[pair(i) for i in range(demos)],
            'test':[pair(100+i) for i in range(4)],'program_solution':program(settings)}

# Stable private shuffle of the complete bank precedes prefix projection.
_raw_generate=generate
def generate(seed,settings,demos,queries):
    if type(queries) is not int or not 1<=queries<=4:raise ValueError("queries must be 1..4")
    ep=_raw_generate(seed,settings,demos,4)
    import random
    random.Random(f"repeat-private-query-order:{seed}").shuffle(ep["test"])
    ep["test"]=ep["test"][:queries]
    return ep
def public_view(ep,index):
    import copy
    return copy.deepcopy(dict(train=[dict(input=p["input"],output=p["output"])for p in ep["train"]],test=[dict(input=ep["test"][index]["input"])]))
