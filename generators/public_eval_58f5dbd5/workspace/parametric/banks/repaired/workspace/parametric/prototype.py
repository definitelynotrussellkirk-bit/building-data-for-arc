"""Native rule/presentation layer over the portable standalone sampler.

The exact task is loaded through the public same-checkout resolver. The canonical
Racket resource is declared in promotion.json and equals root reference.rkt.
"""
from pathlib import Path
import copy
import json
import random
from reviewer_support import find_root, load_selected_generator
TASK_ID='public_eval_58f5dbd5'
HOME=Path(__file__).resolve().parents[2]
import importlib.util, hashlib
_local=Path(__file__).resolve().parents[2]/'generator.py'
_spec=importlib.util.spec_from_file_location('_local_'+hashlib.sha256(str(_local).encode()).hexdigest(),_local)
_base=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_base)
_int=_base._int
_bbox=_base._bbox
analyse=_base.analyse
solve=_base.solve
sample=_base.sample
MODES=_base.MODES

def settings(value):
    if type(value) is not dict or set(value)!= {'stencil_mode'} or type(value['stencil_mode']) is not str or value['stencil_mode'] not in MODES:
        raise ValueError('settings must contain one declared stencil_mode')
    return value['stencil_mode']

def program(value):
    mode=settings(value)
    source=Path(__file__).with_name('canonical.rkt').read_text()
    if mode=='cutout': return source
    return source.replace('punch its occupied cells out of the plate\'s','keep its occupied cells within the plate\'s').replace('(if (member (list rr cc) mask) bg color)','(if (member (list rr cc) mask) color bg)')

def generate(seed,value,demos,queries):
    mode=settings(value);_int(seed,0,2**63-1,'seed');_int(demos,2,6,'demos');_int(queries,4,4,'queries')
    banks={sp:[sample(seed,i) for i in indices] for sp,indices in [('train',range(demos)),('test',range(100,104))]}
    inputs=[g for grids in banks.values() for g in grids]
    if len({json.dumps(g) for g in inputs})!=len(inputs):raise ValueError('duplicate input')
    return {**{sp:[dict(input=g,output=solve(g,mode)) for g in grids] for sp,grids in banks.items()},'program_solution':program(value)}

def public_turns(episode,presentation_seed,stop_after=4):
    _int(presentation_seed,0,2**63-1,'presentation_seed');_int(stop_after,1,4,'stop_after')
    if len(episode['test'])!=4:raise ValueError('materialize the complete four-query bank first')
    # Randomization belongs to the private controller, independent of source order.
    order=list(range(4));random.Random(presentation_seed).shuffle(order)
    return [dict(train=[dict(input=copy.deepcopy(p['input']),output=copy.deepcopy(p['output'])) for p in episode['train']],test=[dict(input=copy.deepcopy(episode['test'][i]['input']))]) for i in order[:stop_after]]

