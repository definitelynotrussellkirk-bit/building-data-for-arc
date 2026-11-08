"""Native marked-path family with independently selected demo/query counts."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import random
import sys
BASE=Path(__file__).resolve().parent
TASK='public_eval_faa9f03d'
VERSION='1.0.0'
MODES=('reverse_marked','preserve_visible')


def local(name):
    p=BASE/(name+'.py');key='_faa_'+name+'_'+hashlib.sha256(str(p).encode()).hexdigest()
    if key not in sys.modules:
        spec=importlib.util.spec_from_file_location(key,p);m=importlib.util.module_from_spec(spec);sys.modules[key]=m;spec.loader.exec_module(m)
    return sys.modules[key]

model=local('model')
sampler=local('sampler')


def setting(settings):
    if type(settings) is not dict or set(settings)!={'crossing_policy'} or settings['crossing_policy'] not in MODES:
        raise ValueError('exact crossing_policy=reverse_marked|preserve_visible required')
    return settings['crossing_policy']


def program(settings):
    return (BASE/('canonical.rkt' if setting(settings)=='reverse_marked' else 'preserve_visible.rkt')).read_text()


def sample_input(seed,index):
    return sampler.scene(seed,index)['input']


def generate(seed,settings,demos,queries):
    mode=setting(settings)
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos must be 2..6')
    if type(queries) is not int or not 1<=queries<=4:raise ValueError('queries must be 1..4')
    def pair(index):
        scene=sampler.scene(seed,index)
        return {'input':scene['input'],'output':scene['outputs'][mode]}
    train=[pair(i)for i in range(demos)];bank=[pair(100+i)for i in range(4)]
    return {'train':train,'test':copy.deepcopy(bank[:queries]),'program_solution':program(settings),
            'settings':copy.deepcopy(settings),'seed':seed,'private':{'query_bank':bank}}


def public_view(episode,turn=0,presentation_seed=0):
    if type(turn) is not int or not 0<=turn<4:raise ValueError('turn must be 0..3')
    if type(presentation_seed) is not int:raise ValueError('presentation seed must be an integer')
    bank=episode['private']['query_bank']
    if len(bank)!=4:raise ValueError('four private queries required')
    order=list(range(4));random.Random(presentation_seed).shuffle(order)
    return {'train':[{'input':copy.deepcopy(p['input']),'output':copy.deepcopy(p['output'])}for p in episode['train']],
            'test':[{'input':copy.deepcopy(bank[order[turn]]['input'])}]}
