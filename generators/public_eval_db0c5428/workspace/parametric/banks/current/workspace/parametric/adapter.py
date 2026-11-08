"""Thin native adapter: setting-neutral inputs and deterministic label claims."""
import importlib.util
from pathlib import Path
BASE=Path(__file__).resolve().parent

def local(name):
    spec=importlib.util.spec_from_file_location('_db0c5428_'+name,BASE/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

CORE=local('prototype');SAMPLER=local('sampler')

def setting(settings):
    if (type(settings) is not dict or set(settings)!={'extension_scope'} or
        type(settings['extension_scope']) is not str or settings['extension_scope'] not in CORE.SCOPES):
        raise ValueError('only a valid extension_scope is accepted')
    return settings['extension_scope']

def program(settings):
    scope=setting(settings)
    return (BASE/('canonical.rkt' if scope=='all' else 'rarest_tip.rkt')).read_text()

def generate(seed,settings,demos,queries):
    scope=setting(settings)
    if type(seed) is not int or type(demos) is not int or not 2<=demos<=6 or type(queries) is not int or queries!=4:
        raise ValueError('exact integer seed, 2..6 demos and exactly four queries required')
    def pair(index):
        g=SAMPLER.generate(seed,index)
        return {'input':g,'output':CORE.solve(g,scope)}
    return {'train':[pair(i) for i in range(demos)],'test':[pair(100+i) for i in range(4)],
            'program_solution':program(settings)}
