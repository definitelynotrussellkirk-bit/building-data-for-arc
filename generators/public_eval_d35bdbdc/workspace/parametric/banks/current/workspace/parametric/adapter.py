"""Portable native adapter: private four-query bank, independent count prefixes."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

HERE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_wire_engine_'+hashlib.sha256(str(HERE).encode()).hexdigest(),HERE/'engine.py')
_engine=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_engine)
predict=_engine.predict
parse=_engine.parse
PARAMETERS={'transfer':['one_hop','follow_chain']}
DEFAULT={'transfer':'one_hop'}

def _mode(settings):
    if type(settings) is not dict or set(settings)!=set(PARAMETERS) or type(settings['transfer']) is not str or settings['transfer'] not in PARAMETERS['transfer']:
        raise ValueError('settings must declare exactly transfer=one_hop or follow_chain')
    return settings['transfer']

def program(settings):
    mode=_mode(settings);text=(HERE/'canonical.rkt').read_text()
    if mode=='one_hop':return text
    return text.replace('(define transfer-policy "one_hop")','(define transfer-policy "follow_chain")',1)

def counterfactual_program():
    return program({'transfer':'follow_chain'}).replace('(resolve (third donor) (- budget 1)', '(resolve (first donor) (- budget 1)',1)

def _integer(n,lo,hi,name):
    if type(n) is not int or not lo<=n<=hi:raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')

def generate(seed,settings,demos,queries):
    _integer(seed,0,2**63-1,'seed');_integer(demos,2,6,'demos');_integer(queries,1,4,'queries');mode=_mode(settings)
    scenes=_engine.bank(seed)
    order=list(range(6,10));random.Random(f'd35bdbdc:presentation:{seed}').shuffle(order)
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
    cert=parse(grid);mapping={b['body']:b['value'] for b in cert['beads']}
    rows=[]
    for i in cert['selected']:
        b=cert['beads'][i];final,visited=_engine.trace(b['value'],mapping)
        rows.append({'receiver_body':b['body'],'initial_pointer':b['value'],
                     'visited_donor_bodies':visited,'terminal':final})
    return rows

DEPENDENCY={
 'step_a':'Follow the gray wire and resolve the selected receiver center to its donor; read that donor center from the original scene.',
 'intermediate':'The input-dependent center color returned by each donor lookup, and the visited-color set for cycle termination.',
 'step_b':'Use each newly read color as the next donor body key until a terminal or repeated color is reached; write the resulting centers into the wire-selected receivers.',
 'why_b_depends_on_a':'The next donor and chain length are scene-dependent, not a fixed palette mapping. Replacing each donor center by its body color breaks the chain and changes the final receiver color.'}
ABLATION='wrong_intermediate'
