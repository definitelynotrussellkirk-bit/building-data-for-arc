"""Bounded native interface. All resources are exact adjacent paths."""
from pathlib import Path
import importlib.util
import hashlib
import sys

BASE=Path(__file__).resolve().parent
_path=BASE/'sampler.py'
_name='_symmetry_sampler_'+hashlib.sha256(str(_path).encode()).hexdigest()[:16]
_spec=importlib.util.spec_from_file_location(_name,_path)
sampler=importlib.util.module_from_spec(_spec);sys.modules[_name]=sampler
_spec.loader.exec_module(sampler)

def _mode(settings):
    if type(settings) is not dict or set(settings)!={'repair_mode'} or settings['repair_mode'] not in ('trim','complete'):
        raise ValueError('settings must declare only repair_mode=trim|complete')
    return settings['repair_mode']

def program(settings):
    return (BASE/('canonical.rkt' if _mode(settings)=='trim' else 'complete.rkt')).read_text()

def predict(grid, settings):
    return sampler.predict(grid,_mode(settings))

def generate(seed,settings,demos,queries):
    mode=_mode(settings)
    if type(seed) is not int or not 0<=seed<2**63:raise ValueError('invalid seed')
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos must be 2..6')
    if type(queries) is not int or queries!=4:raise ValueError('exactly four queries are required')
    def pair(index):
        grid=sampler.sample(seed,index)
        return {'input':grid,'output':sampler.predict(grid,mode)}
    return {'train':[pair(i) for i in range(demos)],
            'test':[pair(100+i) for i in range(4)],'program_solution':program(settings)}
