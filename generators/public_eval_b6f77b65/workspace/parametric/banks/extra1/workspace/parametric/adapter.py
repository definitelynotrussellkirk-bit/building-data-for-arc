"""Native authoring adapter; all labels are claims pending protected execution."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

BASE=Path(__file__).resolve().parent


def _load(filename):
    path=BASE/filename
    raw=path.read_bytes()
    name='_arch_support_native_'+hashlib.sha256(str(path).encode()+raw).hexdigest()
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    exec(compile(raw,str(path),'exec'),module.__dict__)
    return module


family=_load('native_family.py')
sampler=_load('sampler.py')


def program(settings):
    return family.program(settings)


def generate(seed,settings,demos,queries):
    settings=family.normalize_settings(settings)
    for name,value,lo,hi in [('seed',seed,0,2**63-1),('demos',demos,2,6),('queries',queries,1,4)]:
        if type(value) is not int or not lo<=value<=hi:
            raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    demo_bank,query_bank=sampler.sample_banks(seed)
    if len(demo_bank)!=6 or len(query_bank)!=4:
        raise ValueError('sampler must materialize complete six/four banks')
    if len({json.dumps(g,separators=(',',':')) for g in demo_bank+query_bank})!=10:
        raise ValueError('all inputs must be distinct')
    def pair(grid):
        own=family.normalize_grid(grid)
        return {'input':own,'output':family.solve(own,settings)}
    return {'train':[pair(g) for g in demo_bank[:demos]],
            'test':[pair(g) for g in query_bank[:queries]],
            'program_solution':program(settings)}
