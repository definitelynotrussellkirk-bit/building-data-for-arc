"""Native adapter for public 0934a4d8; public views omit private metadata."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_public_eval_0934a4d8_model',HERE/'model.py')
model=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=model;_spec.loader.exec_module(model)


def _mode(settings):
    if type(settings) is not dict or set(settings)!={'output_mode'} or settings['output_mode'] not in model.MODES:
        raise ValueError('settings require exactly output_mode=patch|marker_bbox')
    return settings['output_mode']


def program(settings):
    mode=_mode(settings);source=(HERE/'canonical.rkt').read_text()
    return source if mode=='patch' else source.replace('(define crop-marker #f)','(define crop-marker #t)')


def generate(seed,settings,demos,queries):
    mode=_mode(settings)
    if type(seed) is not int or type(demos) is not int or not 2<=demos<=6 or type(queries) is not int or not 1<=queries<=4:
        raise ValueError('exact integer seed, 2..6 demonstrations and 1..4 queries required')
    train=[model.sample_input(seed,i) for i in range(demos)]
    bank=[model.sample_input(seed,i,query=True) for i in range(4)]
    test=[bank[i] for i in model.query_order(seed)[:queries]]
    return {'train':[{'input':g,'output':model.solve(g,mode)} for g in train],
            'test':[{'input':g,'output':model.solve(g,mode)} for g in test],
            'program_solution':program(settings)}


def public_view(episode,query_index):
    if type(query_index) is not int or not 0<=query_index<len(episode['test']):raise ValueError('invalid query index')
    return {'train':[{'input':deepcopy(p['input']),'output':deepcopy(p['output'])} for p in episode['train']],
            'test':[{'input':deepcopy(episode['test'][query_index]['input'])}]}
