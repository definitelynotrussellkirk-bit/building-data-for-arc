"""Native adapter: claims are independently executed by protected Racket."""
from pathlib import Path
import importlib.util

HERE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_periodic_engine_'+str(HERE),HERE/'engine.py')
engine=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(engine)

def setting(settings):
    if (type(settings) is not dict or set(settings)!={'extent'} or
            type(settings['extent']) is not str or settings['extent'] not in engine.SETTINGS):
        raise ValueError('settings must contain exactly extent=stop_at_hit|continue_after_hit')
    return settings['extent']

def program(settings):
    mode=setting(settings)
    return (HERE/('canonical.rkt' if mode=='stop_at_hit' else 'continue_after_hit.rkt')).read_text()

def generate(seed,settings,demos,queries):
    mode=setting(settings);engine.integer(seed,0,2**63-1,'seed')
    engine.integer(demos,2,6,'demos');engine.integer(queries,1,4,'queries')
    def pairs(kind,count):
        rows=[]
        for i in range(count):
            g=engine.scene(seed,i,kind);rows.append({'input':g,'output':engine.solve(g,mode)})
        return rows
    return {'train':pairs('demo',demos),'test':pairs('query',queries),'program_solution':program(settings)}
