"""Native matched-input family for public parent d59b0160."""
import hashlib,importlib.util,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent

def _load(name):
    path=BASE/f'{name}.py';key='_d59_'+name+'_'+hashlib.sha256(str(path).encode()).hexdigest()[:16]
    if key not in sys.modules:
        spec=importlib.util.spec_from_file_location(key,path);m=importlib.util.module_from_spec(spec);sys.modules[key]=m;spec.loader.exec_module(m)
    return sys.modules[key]
engine=_load('engine')
SETTINGS=tuple({'finish':v} for v in engine.SETTINGS)

def validate_settings(settings):
    if type(settings) is not dict or set(settings)!={'finish'} or type(settings['finish']) is not str or settings['finish'] not in engine.SETTINGS:
        raise ValueError('Expected exactly finish=filter_only|highlight_closest_survivor')
    return settings['finish']

def program(settings):
    finish=validate_settings(settings)
    return (BASE/('canonical.rkt' if finish=='filter_only' else 'highlight.rkt')).read_text()

def generate(seed,settings,demos=3,queries=4):
    engine.integer(seed,0,2**63-1,'seed');engine.integer(demos,2,6,'demos');engine.integer(queries,4,4,'queries')
    finish=validate_settings(settings)
    def pair(kind,index):
        g=engine.scene(seed,kind,index);return {'input':g,'output':engine.solve(g,finish)}
    return {'train':[pair('demo',i) for i in range(demos)],'test':[pair('query',i) for i in range(queries)],'program_solution':program(settings)}
