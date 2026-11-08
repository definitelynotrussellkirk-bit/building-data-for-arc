"""Native gate-path adapter, with independent input and rule-setting streams."""
import hashlib
import importlib.util
from pathlib import Path
import sys
BASE=Path(__file__).resolve().parent

def _load(name):
    path=BASE/(name+'.py');key='_gates_'+name+'_'+hashlib.sha256(str(path).encode()).hexdigest()[:16]
    if key not in sys.modules:
        spec=importlib.util.spec_from_file_location(key,path);mod=importlib.util.module_from_spec(spec);sys.modules[key]=mod;spec.loader.exec_module(mod)
    return sys.modules[key]

model=_load('model');sampler=_load('sampler')
SETTINGS=({'flow':'down'},{'flow':'up'})

def validate_settings(settings):
    if type(settings) is not dict or set(settings)!={'flow'} or type(settings['flow']) is not str or settings['flow'] not in ('down','up'):
        raise ValueError('Expected exactly flow=down|up')
    return settings['flow']


def program(settings):
    flow=validate_settings(settings)
    return (BASE/('canonical.rkt' if flow=='down' else 'up.rkt')).read_text()


def generate(seed,settings,demos=3,queries=4):
    sampler.integer(seed,0,2**63-1,'seed');sampler.integer(demos,2,6,'demos');sampler.integer(queries,4,4,'queries')
    flow=validate_settings(settings)
    def pair(split,index):
        g=sampler.draw(seed,index,split=split)
        return {'input':g,'output':model.solve(g,flow)}
    return {'train':[pair('train',i) for i in range(demos)],'test':[pair('test',i) for i in range(queries)],'program_solution':program(settings)}
