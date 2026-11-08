"""Native adapter: execute labels independently before promotion."""
import importlib.util
from pathlib import Path
BASE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_holes_model_'+str(BASE).encode().hex(),BASE/'model.py')
model=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(model)
SETTINGS=({'fill_scope':'all'},{'fill_scope':'largest_per_color'})


def checked(settings):
    if type(settings) is not dict or set(settings)!={'fill_scope'} or type(settings['fill_scope']) is not str or settings not in SETTINGS:
        raise ValueError('expected fill_scope=all or largest_per_color')
    return settings['fill_scope']


def program(settings):
    scope=checked(settings);source=(BASE/'canonical.rkt').read_text()
    if scope=='all':return source
    old="(define fill-scope 'all)"
    if source.count(old)!=1:raise ValueError('canonical declaration missing')
    return source.replace(old,"(define fill-scope 'largest_per_color)")


def generate(seed,settings,demos=3,queries=4):
    scope=checked(settings)
    model.integer(seed,0,2**63-1,'seed');model.integer(demos,2,6,'demos');model.integer(queries,4,4,'queries')
    def pair(i,query):
        grid=model.scene(seed,i,query=query)
        return {'input':grid,'output':model.solve(grid,scope)}
    return {'train':[pair(i,False) for i in range(demos)],'test':[pair(i,True) for i in range(4)],'program_solution':program(settings)}
