"""Native bounded adapter; sampling never depends on hidden count_scope."""
from pathlib import Path
import importlib.util
BASE=Path(__file__).resolve().parent

def local(name):
    s=importlib.util.spec_from_file_location('_58490d8a_'+name,BASE/(name+'.py'))
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

CORE=local('prototype');SAMPLER=local('sampler')

def setting(settings):
    if (type(settings) is not dict or set(settings)!={'count_scope'} or
        type(settings['count_scope']) is not str or settings['count_scope'] not in CORE.SCOPES):
        raise ValueError('only a valid count_scope is accepted')
    return settings['count_scope']

def program(settings):
    return (BASE/('canonical.rkt' if setting(settings)=='all' else 'largest_per_color.rkt')).read_text()

def generate(seed,settings,demos,queries):
    scope=setting(settings)
    if type(seed) is not int or type(demos) is not int or not 2<=demos<=6 or type(queries) is not int or queries!=4:
        raise ValueError('exact integer seed, 2..6 demos and exactly four queries required')
    def pair(index):
        g=SAMPLER.generate(seed,index);return {'input':g,'output':CORE.solve(g,scope)}
    return {'train':[pair(i) for i in range(demos)],'test':[pair(100+i) for i in range(4)],'program_solution':program(settings)}
