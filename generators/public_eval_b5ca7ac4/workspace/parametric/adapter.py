"""Exact adjacent native resources; no catalog/gold/sibling imports."""
from pathlib import Path
import importlib.util,sys
BASE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_b5ca7ac4_prototype',BASE/'prototype.py')
P=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=P;_spec.loader.exec_module(P)

def _setting(settings):
    if type(settings) is not dict or set(settings)!={'packing_order'} or type(settings['packing_order']) is not str or settings['packing_order'] not in P.SETTINGS:
        raise ValueError('Expected exactly packing_order=front_first|top_first')
    return settings['packing_order']

def program(settings):
    key=_setting(settings)
    return (BASE/('canonical.rkt' if key=='front_first' else 'top_first.rkt')).read_text()

def generate(seed,settings,demos=2,queries=4):
    key=_setting(settings);P.validate_request(seed,demos,queries)
    def pair(index,query=False):
        g=P.scene(seed,index,query=query)
        return {'input':g,'output':P.solve(g,key)}
    return {'train':[pair(i) for i in range(demos)],'test':[pair(i,True) for i in range(queries)],'program_solution':program(settings)}
