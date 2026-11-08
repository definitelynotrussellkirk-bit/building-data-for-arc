"""Native entrypoint with independent count limits and matched setting inputs."""
import hashlib
import importlib.util
from pathlib import Path

HOME=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('family_142_'+hashlib.sha256(str(HOME).encode()).hexdigest(),HOME/'family.py')
family=importlib.util.module_from_spec(s);s.loader.exec_module(family)


def _mode(settings):
    if type(settings) is not dict or set(settings)!={'mode'} or type(settings['mode']) is not str or settings['mode'] not in family.MODES:
        raise ValueError('settings must contain exactly one declared mode')
    return settings['mode']


def program(settings):
    mode=_mode(settings)
    return (HOME/'rules'/('canonical.rkt' if mode=='caps' else 'residual_largest.rkt')).read_text()


def generate(seed,settings,demos,queries):
    mode=_mode(settings)
    for name,value,lo,hi in [('seed',seed,0,2**63-1),('demos',demos,2,6),('queries',queries,1,4)]:
        if type(value) is not int or not lo<=value<=hi:raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    train,test=family.input_bank(seed)
    def pairs(gs):return [{'input':g,'output':family.solve(g,mode)} for g in gs]
    return {'train':pairs(train[:demos]),'test':pairs(test[:queries]),'program_solution':program(settings),'settings':dict(settings)}
