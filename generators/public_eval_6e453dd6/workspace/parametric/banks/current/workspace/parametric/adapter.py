"""Native adapter. All executable resources are adjacent and source-bound."""
from pathlib import Path
import copy
import importlib.util
import sys

BASE=Path(__file__).resolve().parent
_name='_cavity_projection_core_'+str(BASE).encode().hex()
_spec=importlib.util.spec_from_file_location(_name,BASE/'core.py')
CORE=importlib.util.module_from_spec(_spec); sys.modules[_name]=CORE; _spec.loader.exec_module(CORE)


def setting(settings):
    if type(settings) is not dict or set(settings)!={'projection'} or type(settings['projection']) is not str or settings['projection'] not in CORE.MODES:
        raise ValueError('Declare exactly projection=all or largest_hole')
    return settings['projection']


def program(settings):
    mode=setting(settings)
    return (BASE/('canonical.rkt' if mode=='all' else 'largest_hole.rkt')).read_text()


def source_order(seed):
    CORE.integer(seed,0,2**63-1,'seed'); order=list(range(4))
    CORE.rng(seed,'presentation').shuffle(order)
    return order


def generate(seed,settings,demos=2,queries=4):
    mode=setting(settings); CORE.integer(seed,0,2**63-1,'seed')
    CORE.integer(demos,2,6,'demos'); CORE.integer(queries,1,4,'queries')
    train=[{'input':CORE.build(seed,i)} for i in range(6)]
    bank=[{'input':CORE.build(seed,100+i)} for i in range(4)]
    for p in train+bank: p['output']=CORE.solve(p['input'],mode)
    return {'train':train[:demos],'test':[bank[i] for i in source_order(seed)][:queries],
            'program_solution':program(settings)}


def public_view(episode,index=0):
    CORE.integer(index,0,len(episode['test'])-1,'index')
    return {'train':[{'input':CORE.grid(p['input']),'output':CORE.grid(p['output'])} for p in episode['train']],
            'test':[{'input':CORE.grid(episode['test'][index]['input'])}]}
