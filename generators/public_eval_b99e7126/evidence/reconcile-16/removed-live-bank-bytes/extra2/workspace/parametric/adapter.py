"""Portable native adapter: private four-query bank, independent count prefixes."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

HERE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_tile_engine_'+hashlib.sha256(str(HERE).encode()).hexdigest(),HERE/'engine.py')
_engine=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_engine)
predict=_engine.predict
parse=_engine.parse
PARAMETERS={'completion':['complete','fill_holes']}
DEFAULT={'completion':'complete'}

def _mode(settings):
    if type(settings) is not dict or set(settings)!=set(PARAMETERS) or type(settings['completion']) is not str or settings['completion'] not in PARAMETERS['completion']:
        raise ValueError('settings must declare exactly completion=complete or fill_holes')
    return settings['completion']

def program(settings):
    mode=_mode(settings);text=(HERE/'canonical.rkt').read_text()
    if mode=='complete':return text
    return text.replace('(define completion-policy "complete")','(define completion-policy "fill_holes")',1)

def counterfactual_program():
    return program({'completion':'fill_holes'}).replace('(define completion-policy "fill_holes")', '(define completion-policy "fill_before")', 1)


def _integer(n,lo,hi,name):
    if type(n) is not int or not lo<=n<=hi:raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')

def generate(seed,settings,demos,queries):
    _integer(seed,0,2**63-1,'seed');_integer(demos,2,6,'demos');_integer(queries,1,4,'queries');mode=_mode(settings)
    scenes=_engine.bank(seed)
    order=list(range(6,10));random.Random(f'b99e7126:presentation:{seed}').shuffle(order)
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
    cert=parse(grid);e=_engine
    return {'anchor':list(cert['anchor']),'decoded_mask':sorted(map(list,cert['mask'])),
            'partial_macro_cells':sorted(map(list,cert['observed'])),
            'completed_macro_cells':sorted(map(list,cert['target'])),
            'holes_before':sorted(map(list,e.holes(cert['observed'],*cert['shape']))),
            'holes_after':sorted(map(list,e.holes(cert['target'],*cert['shape'])))}

DEPENDENCY={
 'step_a':'Decode the unique novel-color micro-mask, align it uniquely to the observed special tiles, and complete its macro-scale copy.',
 'intermediate':'The completed occupied macro-cell set, including the newly inserted copies of the special tile.',
 'step_b':'Flood the complement of that completed set from the macro-grid boundary using four-neighbor connectivity, and fill the enclosed macro-cells with the special tile.',
 'why_b_depends_on_a':'Missing boundary tiles can leave a cavity open. Flooding the partial arrangement first classifies it as exterior and misses a pocket closed only by template completion.'}
ABLATION='wrong_order'
