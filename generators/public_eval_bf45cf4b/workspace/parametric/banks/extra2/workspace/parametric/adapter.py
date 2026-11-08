"""Native, matched-input motif expansion family. No import from another task or checkout."""
import hashlib
import importlib.util
from pathlib import Path
import sys

BASE=Path(__file__).resolve().parent

def _load(name):
    path=BASE/(name+'.py');key='_motif_'+name+'_'+hashlib.sha256(str(path).encode()).hexdigest()[:16]
    if key not in sys.modules:
        spec=importlib.util.spec_from_file_location(key,path);mod=importlib.util.module_from_spec(spec)
        sys.modules[key]=mod;spec.loader.exec_module(mod)
    return sys.modules[key]

model=_load('model');sampler=_load('sampler')
SETTINGS=({'finish':'expand_only'},{'finish':'highlight_largest'})

def validate_settings(settings):
    if type(settings) is not dict or set(settings)!={'finish'} or type(settings['finish']) is not str or settings['finish'] not in ('expand_only','highlight_largest'):
        raise ValueError('Expected exactly finish=expand_only|highlight_largest')
    return settings['finish']


def program(settings):
    finish=validate_settings(settings)
    return (BASE/('canonical.rkt' if finish=='expand_only' else 'highlight.rkt')).read_text()


def generate(seed,settings,demos=3,queries=4):
    sampler.integer(seed,0,2**63-1,'seed');sampler.integer(demos,2,6,'demos');sampler.integer(queries,4,4,'queries')
    finish=validate_settings(settings)
    def pair(split,index):
        g=sampler.draw(seed,index,split=split)
        return {'input':g,'output':model.solve(g,finish)}
    return {'train':[pair('train',i) for i in range(demos)],
            'test':[pair('test',i) for i in range(queries)],'program_solution':program(settings)}
