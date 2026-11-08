"""Portable native adapter: private four-query bank, independent count prefixes."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

HERE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_palette_engine_'+hashlib.sha256(str(HERE).encode()).hexdigest(),HERE/'engine.py')
_engine=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_engine)
predict=_engine.predict
parse=_engine.parse
PARAMETERS={'erasure':['matching','palette_cascade']}
DEFAULT={'erasure':'matching'}

def _mode(settings):
    if type(settings) is not dict or set(settings)!=set(PARAMETERS) or type(settings['erasure']) is not str or settings['erasure'] not in PARAMETERS['erasure']:
        raise ValueError('settings must declare exactly erasure=matching or palette_cascade')
    return settings['erasure']

def program(settings):
    mode=_mode(settings);text=(HERE/'canonical.rkt').read_text()
    if mode=='matching':return text
    return text.replace('(define erase-policy "matching")','(define erase-policy "palette_cascade")',1)

def counterfactual_program():
    return program({'erasure':'palette_cascade'}).replace('(define initial-scope "seeds")','(define initial-scope "global")',1)

def _integer(n,lo,hi,name):
    if type(n) is not int or not lo<=n<=hi:raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')

def generate(seed,settings,demos,queries):
    _integer(seed,0,2**63-1,'seed');_integer(demos,2,6,'demos');_integer(queries,1,4,'queries');mode=_mode(settings)
    scenes=_engine.bank(seed)
    order=list(range(6,10));random.Random(f'd59b0160:presentation:{seed}').shuffle(order)
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
    cert=parse(grid);selected,waves=_engine.cascade(cert)
    return {'key_colors':sorted(cert['keys']),'seed_panels':cert['seeds'],
            'propagation_waves':waves,'selected_panels':sorted(selected)}

DEPENDENCY={
 'step_a':'Find 4-connected panels containing every distinct color in the framed key, then recover their non-key marker palettes.',
 'intermediate':'The input-dependent set of active non-key colors and newly reached panels after each propagation wave.',
 'step_b':'Use the active colors to reach and erase further panels, extend the active palette, and repeat to closure.',
 'why_b_depends_on_a':'A panel missing a key color is erased only when a palette path from a complete-key seed reaches it. Disconnected panels sharing only key colors remain. Activating all visible non-key colors instead erases disconnected decoys.'}
ABLATION='wrong_intermediate'
