"""Thin native adapter: exact local resources, no catalog or private-gold dependency."""
from pathlib import Path
import importlib.util
import sys

BASE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_dfadab01_prototype',BASE/'prototype.py')
P=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=P;_spec.loader.exec_module(P)

def _setting(settings):
    if type(settings) is not dict or set(settings)!={'finish_rule'} or type(settings['finish_rule']) is not str or settings['finish_rule'] not in P.SETTINGS:
        raise ValueError('Expected exactly finish_rule=decode|highlight_largest')
    return settings['finish_rule']

def program(settings):
    key=_setting(settings)
    return (BASE/('canonical.rkt' if key=='decode' else 'highlight_largest.rkt')).read_text()

def generate(seed, settings, demos=2, queries=4):
    key=_setting(settings);P.validate_request(seed,demos,queries)
    def pair(i,query=False):
        g=P.scene(seed,i,query=query)
        return {'input':g,'output':P.solve(g,key)}
    return {'train':[pair(i) for i in range(demos)],'test':[pair(i,True) for i in range(queries)],'program_solution':program(settings)}
