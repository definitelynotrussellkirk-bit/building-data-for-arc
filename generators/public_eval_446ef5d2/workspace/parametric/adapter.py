"""Native adapter: all executable resources stay in this directory."""
from pathlib import Path
from copy import deepcopy
import importlib.util
import random

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_core_446ef5d2',HERE/'core.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
PARAMETERS=core.PARAMETERS
DEFAULT=core.DEFAULT
predict=core.predict
solve=core.solve
parse=core.parse
validate_grid=core.validate_grid

def settings_mode(settings):
    if type(settings) is not dict or set(settings)!={'mode'} or type(settings['mode']) is not str or settings['mode'] not in PARAMETERS['mode']:
        raise ValueError('undeclared settings')
    return settings['mode']

def program(settings):
    mode=settings_mode(settings);source=(HERE/'canonical.rkt').read_text()
    return source if mode=='assembly' else source.replace('(define mode "assembly")',f'(define mode "{mode}")',1)

def rival_program(name):
    if name not in ('assembly','raw_largest','smallest_region','first_region','all_regions'):raise ValueError('no Racket rival declared')
    return program(DEFAULT).replace('(define mode "assembly")',f'(define mode "{name}")',1)

def generate(seed,settings,demos=2,queries=4):
    mode=settings_mode(settings)
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos in 2..6 required')
    if type(queries) is not int or not 1<=queries<=4:raise ValueError('queries in 1..4 required')
    scenes=core.bank(seed);order=list(range(4));random.Random(f'446ef5d2:presentation:{seed}').shuffle(order)
    def pair(s):return {'input':deepcopy(s['input']),'output':deepcopy(s[mode])}
    return {'train':[pair(s) for s in scenes[:demos]],'test':[pair(scenes[6+i]) for i in order[:queries]],
            'program_solution':program(settings),'private':{'settings':deepcopy(settings),'seed':seed,
                'query_permutation':order,'profiles':deepcopy([s['profile'] for s in scenes])}}

def public_turn(episode,index):
    if type(index) is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
    view={'train':[{'input':deepcopy(p['input']),'output':deepcopy(p['output'])} for p in episode['train']],
          'test':[{'input':deepcopy(episode['test'][index]['input'])}]}
    for pair in view['train']:
        validate_grid(pair['input']);validate_grid(pair['output'])
    validate_grid(view['test'][0]['input']);return view
