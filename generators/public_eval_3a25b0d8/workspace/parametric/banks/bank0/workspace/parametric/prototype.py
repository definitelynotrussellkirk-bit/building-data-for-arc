"""Native rule/presentation layer over the portable standalone sampler.

The exact task is loaded through the public same-checkout resolver. The canonical
Racket resource is declared in promotion.json and equals root reference.rkt.
"""
from pathlib import Path
import copy
import json
import random
from reviewer_support import find_root, load_selected_generator
TASK_ID='public_eval_3a25b0d8'
HOME=Path(__file__).resolve().parents[2]
import importlib.util
_spec=importlib.util.spec_from_file_location('_local_region_base',HOME/'generator.py')
_base=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_base)
_int=_base._int
bbox=_base.bbox
spatial_key=_base.spatial_key
regions=_base.regions
analyse=_base.analyse
solve=_base.solve
_figure=_base._figure
sample=_base.sample
SCOPES=_base.SCOPES

def settings(value):
    if type(value) is not dict or set(value)!={'transfer_scope'} or type(value['transfer_scope']) is not str or value['transfer_scope'] not in SCOPES:
        raise ValueError('settings must name one declared transfer_scope')
    return value['transfer_scope']

def program(value):
    scope=settings(value);code=Path(__file__).with_name('canonical.rkt').read_text()
    if scope=='all':return code
    return code.replace('(define paint? #t)','(define paint? (> (length target-region) (length source-region)))')

def generate(seed,value,demos,queries):
    scope=settings(value);_int(seed,0,2**63-1,'seed');_int(demos,2,6,'demos');_int(queries,4,4,'queries')
    banks={sp:[sample(seed,i) for i in indices] for sp,indices in [('train',range(demos)),('test',range(100,104))]}
    allinputs=[g for grids in banks.values() for g in grids]
    if len({json.dumps(g) for g in allinputs})!=len(allinputs):raise ValueError('duplicate inputs')
    return {**{sp:[dict(input=g,output=solve(g,scope)) for g in grids] for sp,grids in banks.items()},'program_solution':program(value)}

def public_turns(episode,presentation_seed,stop_after=4):
    _int(presentation_seed,0,2**63-1,'presentation_seed');_int(stop_after,1,4,'stop_after')
    if len(episode['test'])!=4:raise ValueError('materialize the complete query bank first')
    order=list(range(4));random.Random(presentation_seed).shuffle(order)
    return [dict(train=[dict(input=copy.deepcopy(p['input']),output=copy.deepcopy(p['output'])) for p in episode['train']],test=[dict(input=copy.deepcopy(episode['test'][i]['input']))]) for i in order[:stop_after]]

