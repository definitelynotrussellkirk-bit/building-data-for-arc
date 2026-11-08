"""Native family interface; all executable resources are adjacent."""
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_d59_family_'+str(HERE),HERE/'family.py')
family=importlib.util.module_from_spec(spec);spec.loader.exec_module(family)
MODES=('erase','largest_survivor')
def setting(settings):
    if type(settings) is not dict or set(settings)!={'finish'} or type(settings['finish']) is not str or settings['finish'] not in MODES:
        raise ValueError('exact finish setting required')
    return settings['finish']
def program(settings):
    mode=setting(settings)
    return (HERE/('canonical.rkt' if mode=='erase' else 'largest_survivor.rkt')).read_text()
def generate(seed,settings,demos=2,queries=4):
    mode=setting(settings)
    for name,value,lo,hi in [('seed',seed,0,2**63-1),('demos',demos,2,6),('queries',queries,1,4)]:
        if type(value) is not int or not lo<=value<=hi:raise ValueError(f'invalid {name}')
    train,test=family.bank(seed)
    pairs=lambda gs:[{'input':g,'output':family.solve(g,mode)} for g in gs]
    return {'train':pairs(train[:demos]),'test':pairs(test[:queries]),'program_solution':program(settings)}
