"""Native resource-closed adapter; labels are claims checked by protected Racket."""
from pathlib import Path
import importlib.util

HERE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_symmetry_engine_'+str(HERE),HERE/'engine.py')
engine=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(engine)

def setting(value):
    if type(value) is not dict or set(value)!={'axis'} or type(value['axis']) is not str or value['axis'] not in engine.SETTINGS:
        raise ValueError('settings must contain exactly axis=vertical|horizontal')
    return value['axis']

def program(settings):
    return (HERE/('canonical.rkt' if setting(settings)=='vertical' else 'horizontal.rkt')).read_text()

def generate(seed, settings, demos, queries):
    mode=setting(settings)
    engine.integer(seed,0,2**63-1,'seed');engine.integer(demos,2,6,'demos');engine.integer(queries,1,4,'queries')
    def pairs(kind,count):
        result=[]
        for i in range(count):
            g=engine.scene(seed,i,kind)
            result.append({'input':g,'output':engine.solve(g,mode)})
        return result
    return {'train':pairs('demo',demos),'test':pairs('query',queries),'program_solution':program(settings)}
