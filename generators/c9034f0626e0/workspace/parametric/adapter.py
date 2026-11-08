"""Four exact rules with two seed-selected authored lattice curricula."""
from pathlib import Path
import importlib.util
import sys
HOME=Path(__file__).resolve().parent

def _load(relative,label):
    p=HOME/relative;s=importlib.util.spec_from_file_location('_c903_union_'+label,p)
    m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);return m
PARITY=_load('parity_adapter.py','parity')
AREA=_load('area/adapter.py','area')
core=PARITY.core
MODES=('period2','period3','ray_size','ray_area_plus_one')

def _mode(settings):
    if (type(settings) is not dict or set(settings)!={'lattice_rule'}
            or type(settings['lattice_rule']) is not str or settings['lattice_rule'] not in MODES):
        raise ValueError('settings must declare exactly one supported lattice_rule')
    return settings['lattice_rule']

def program(settings):
    mode=_mode(settings)
    if mode=='ray_area_plus_one':return AREA.program({'spacing_rule':'ray_component'})
    return PARITY.program(settings)

def generate(seed,settings,demos=3,queries=4):
    mode=_mode(settings)
    core._integer(seed,0,2**63-1,'seed');core._integer(demos,2,6,'demos');core._integer(queries,1,4,'queries')
    # Cross-curriculum mixing failed finite teaching checks. Preserve each
    # rule's source curriculum until a stronger shared curriculum is authored.
    if mode!='ray_area_plus_one':
        original=PARITY.generate(seed,{'lattice_rule':mode},demos,queries)
    else:
        original=AREA.generate(seed,{'spacing_rule':'ray_component'},demos,queries)
    grids={s:[p['input'] for p in original[s]] for s in ('train','test')}
    solve=(lambda g:AREA._module.solve(g,'ray_component')) if mode=='ray_area_plus_one' else (lambda g:core.mirror(g,mode))
    return {**{s:[{'input':g,'output':solve(g)} for g in grids[s]] for s in ('train','test')},'program_solution':program(settings)}

def public_challenge(episode,query_index=None):return PARITY.public_challenge(episode,query_index)
