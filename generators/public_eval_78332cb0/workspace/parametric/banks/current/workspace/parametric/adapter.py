"""Portable native adapter: private four-query bank, independent count prefixes."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

HERE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_chain_engine_'+hashlib.sha256(str(HERE).encode()).hexdigest(),HERE/'engine.py')
_engine=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_engine)
predict=_engine.predict
parse=_engine.parse
PARAMETERS={'counting':['canonical','prefix_parity']}
DEFAULT={'counting':'canonical'}

def _mode(settings):
    if type(settings) is not dict or set(settings)!=set(PARAMETERS) or type(settings['counting']) is not str or settings['counting'] not in PARAMETERS['counting']:
        raise ValueError('settings must declare exactly counting=canonical or prefix_parity')
    return settings['counting']

def program(settings):
    mode=_mode(settings);text=(HERE/'canonical.rkt').read_text()
    if mode=='canonical':return text
    return text.replace('(define count-policy "canonical")','(define count-policy "prefix_parity")',1)

def counterfactual_program():
    return program({'counting':'prefix_parity'}).replace('(define prefix-scope "assembled")','(define prefix-scope "input")',1)

def _integer(n,lo,hi,name):
    if type(n) is not int or not lo<=n<=hi:raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')

def generate(seed,settings,demos,queries):
    _integer(seed,0,2**63-1,'seed');_integer(demos,2,6,'demos');_integer(queries,1,4,'queries');mode=_mode(settings)
    scenes=_engine.bank(seed)
    order=list(range(6,10));random.Random(f'78332cb0:presentation:{seed}').shuffle(order)
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
    p=parse(grid);total=0;sums=[]
    for i in p['order']:total+=p['areas'][i];sums.append(total)
    return {'axis':p['axis'],'chain':p['order'],'input_areas':p['areas'],'assembled_prefix_sums':sums}

DEPENDENCY={
 'step_a':'Reconstruct the unique horizontal or vertical head-to-tail chain by exact border-contact-set matching.',
 'intermediate':'The input-dependent tile order and cumulative foreground counts along that recovered order.',
 'step_b':'Highlight each assembled tile whose cumulative count is odd, retaining all other tile colors.',
 'why_b_depends_on_a':'The same tile has a different prefix count under a different chain order. The counterfactual preserves the correct assembled geometry but computes each tile prefix in scrambled input order, changing which complete tiles are highlighted.'}
ABLATION='wrong_intermediate'
