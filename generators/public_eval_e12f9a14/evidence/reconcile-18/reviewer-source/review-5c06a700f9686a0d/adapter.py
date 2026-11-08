"""Unapproved beam-family candidate: one parent label remains unresolved."""
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('_e12_family_'+str(HERE),HERE/'family.py');family=importlib.util.module_from_spec(s);s.loader.exec_module(family)
MODES=('trace','mark_merged')
def setting(settings):
    if type(settings) is not dict or set(settings)!={'finish'} or type(settings['finish']) is not str or settings['finish'] not in MODES:raise ValueError('exact finish setting required')
    return settings['finish']
def program(settings):
    mode=setting(settings);return (HERE/('canonical.rkt' if mode=='trace' else 'mark_merged.rkt')).read_text()
def generate(seed,settings,demos=2,queries=4):
    mode=setting(settings)
    for name,value,lo,hi in [('seed',seed,0,2**63-1),('demos',demos,2,6),('queries',queries,1,4)]:
        if type(value) is not int or not lo<=value<=hi:raise ValueError(f'invalid {name}')
    tr,te=family.bank(seed)
    pairs=lambda gs:[{'input':g,'output':family.solve(g,mode)} for g in gs]
    return {'train':pairs(tr[:demos]),'test':pairs(te[:queries]),'program_solution':program(settings)}
