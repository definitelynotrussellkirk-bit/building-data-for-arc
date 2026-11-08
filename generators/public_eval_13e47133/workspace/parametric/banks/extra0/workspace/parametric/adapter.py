"""Native inward-band adapter; the real Racket worker verifies all claim labels."""
import importlib.util
from pathlib import Path
BASE=Path(__file__).resolve().parent


def _local(name):
    s=importlib.util.spec_from_file_location('_rings_'+name,BASE/(name+'.py'))
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

CORE=_local('prototype');SAMPLER=_local('sampler')


def _setting(settings):
    if type(settings) is not dict or set(settings)!={'propagation'} or type(settings['propagation']) is not str or settings['propagation'] not in ('cyclic','bouncing'):
        raise ValueError('settings must contain only valid propagation')
    return settings['propagation']


def program(settings):
    value=_setting(settings)
    return (BASE/('canonical.rkt' if value=='cyclic' else 'bouncing.rkt')).read_text()


def generate(seed,settings,demos,queries):
    value=_setting(settings)
    if type(seed) is not int or seed<0 or type(demos) is not int or not 2<=demos<=6 or type(queries) is not int or queries!=4:
        raise ValueError('integer seed, 2..6 demonstrations and exactly four queries required')
    def pair(index):
        g=SAMPLER.generate(seed,index)
        return {'input':g,'output':CORE.solve(g,value)}
    return {'train':[pair(i) for i in range(demos)],'test':[pair(100+i) for i in range(4)],'program_solution':program(settings)}
