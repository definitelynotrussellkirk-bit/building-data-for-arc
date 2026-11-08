"""Four exact orientation rules with seed-selected complementary curricula."""
from pathlib import Path
import importlib.util
import sys
HOME=Path(__file__).resolve().parent

def _load(name):
    p=HOME/(name+'.py');s=importlib.util.spec_from_file_location('_cf5_mixture_'+name,p)
    m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);return m
ORIGINAL=_load('original_adapter')
SUPPLEMENTAL=_load('supplemental_adapter')
_prototype=ORIGINAL._prototype

def branch(seed):
    _prototype._integer('seed',seed,0,2**63-1)
    return 'original' if seed%2==0 else 'supplemental'

def program(settings):return ORIGINAL.program(settings)

def generate(seed,settings,demos,queries):
    program(settings)
    for name,value,lo,hi in (('seed',seed,0,2**63-1),('demos',demos,2,6),('queries',queries,1,4)):
        _prototype._integer(name,value,lo,hi)
    sampler=ORIGINAL if branch(seed)=='original' else SUPPLEMENTAL
    result=sampler.generate(seed,settings,demos,queries)
    # Reuse the existing full bank on the minimum core, under every setting.
    # This selection guard sees no queries and is independent of hidden rule.
    inputs=[p['input'] for p in result['train'][:2]]
    wrong=[_prototype.shortcut_outputs(g,SUPPLEMENTAL._GENERATOR) for g in inputs]
    gold=[SUPPLEMENTAL._all_outputs(g) for g in inputs]
    for orientation in _prototype.SETTINGS:
        survivors=[name for name in wrong[0] if all(
            wrong[i][name]==gold[i][orientation] for i in range(2))]
        if survivors:
            raise RuntimeError('minimum teaching core does not refute full shortcut bank: '+str(survivors))
    return result
