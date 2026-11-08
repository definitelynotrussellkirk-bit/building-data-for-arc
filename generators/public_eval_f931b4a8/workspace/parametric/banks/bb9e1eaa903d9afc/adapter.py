"""Portable native adapter: private four-query bank, independent count prefixes."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

HERE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_stencil_engine_'+hashlib.sha256(str(HERE).encode()).hexdigest(),HERE/'engine.py')
_engine=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_engine)
predict=_engine.predict
parse=_engine.parse
PARAMETERS={'backing':['raster','snake']}
DEFAULT={'backing':'raster'}

def _mode(settings):
    if type(settings) is not dict or set(settings)!=set(PARAMETERS) or type(settings['backing']) is not str or settings['backing'] not in PARAMETERS['backing']:
        raise ValueError('settings must declare exactly backing=raster or snake')
    return settings['backing']

def program(settings):
    mode=_mode(settings);text=(HERE/'canonical.rkt').read_text()
    if mode=='raster':return text
    return text.replace('(define backing-policy "raster")','(define backing-policy "snake")',1)

def counterfactual_program():
    return program({'backing':'snake'}).replace('(define period-policy "primitive")','(define period-policy "raw")',1)

def _integer(n,lo,hi,name):
    if type(n) is not int or not lo<=n<=hi:raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')

def generate(seed,settings,demos,queries):
    _integer(seed,0,2**63-1,'seed');_integer(demos,2,6,'demos');_integer(queries,1,4,'queries');mode=_mode(settings)
    scenes=_engine.bank(seed)
    order=list(range(6,10));random.Random(f'f931b4a8:presentation:{seed}').shuffle(order)
    def pair(i):return {'input':deepcopy(scenes[i][0]),'output':predict(scenes[i][0],mode)}
    return {'train':[pair(i) for i in range(demos)],'test':[pair(i) for i in order[:queries]],
            'program_solution':program(settings),'private':{'settings':deepcopy(settings),'query_permutation':order,
            'profiles':[deepcopy(scenes[i][1]) for i in range(demos)]+[deepcopy(scenes[i][1]) for i in order[:queries]]}}

def public_turn(episode,index=0):
    if type(index) is not int or not 0<=index<len(episode['test']):raise ValueError('invalid current query index')
    return {'train':[{'input':deepcopy(p['input']),'output':deepcopy(p['output'])} for p in episode['train']],
            'test':[{'input':deepcopy(episode['test'][index]['input'])}]}

def rivals():
    return [p for p in _engine.POLICIES]


def causal_metadata(grid):
    p=parse(grid)
    return {'primitive_period':p['period'],'raw_quadrant_shape':[p['qh'],p['qw']],
            'output_shape':[p['height'],p['width']]}

DEPENDENCY={
 'step_a':'Recover the smallest exact row and column repeat periods of the transparent stencil.',
 'intermediate':'The input-dependent primitive stencil height and width, distinct from the raw quadrant dimensions.',
 'step_b':'Use the primitive periods to partition output into stencil copies and address the backing color for each copy, reversing odd backing rows in snake mode.',
 'why_b_depends_on_a':'The same transparent output cell addresses a different backing cell when the intermediate period is wrong. The counterfactual keeps the tiled stencil pixels and output dimensions unchanged but uses raw quadrant dimensions for addressing.'}
ABLATION='wrong_intermediate'
