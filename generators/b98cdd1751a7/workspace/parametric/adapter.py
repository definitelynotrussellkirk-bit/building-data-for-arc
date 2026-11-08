"""Three exact ordering rules with shared two-demo teaching and mixed queries."""
from pathlib import Path
from copy import deepcopy
from functools import lru_cache
import importlib.util
import sys
HOME=Path(__file__).resolve().parent

def _load(relative,label):
    p=HOME/relative;s=importlib.util.spec_from_file_location('_b98_union_'+label,p)
    m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);return m
COLOR=_load('color_adapter.py','color')
FEWEST=_load('fewest/adapter.py','fewest')
VALUES=('left_right','match_top_left_color','fewest_cells_first')

def _mode(settings):
    if type(settings) is not dict or set(settings)!={'bottom_order'} or type(settings['bottom_order']) is not str or settings['bottom_order'] not in VALUES:
        raise ValueError('settings must name one supported bottom_order')
    return settings['bottom_order']

def program(settings):
    mode=_mode(settings)
    if mode=='fewest_cells_first':return FEWEST.program({'within_group_order':'fewest_cells_first'})
    return COLOR.program(settings)

@lru_cache(maxsize=64)
def _inputs(seed):
    COLOR._native._integer(seed,0,2**63-1,'seed')
    old=COLOR._native.sample_inputs(seed,6,4)
    incoming=FEWEST._episode_inputs(seed,6)
    _,_,old_top,_=FEWEST._validate_objects(old['train'][0])
    old_top=sorted(old_top,key=lambda o:o['col0'])
    cue,other=[o['color'] for o in old_top]
    witness=deepcopy(incoming['train'][0])
    _,_,upper,lower=FEWEST._validate_objects(witness)
    for group in (upper,lower):
        for obj,color in zip(sorted(group,key=lambda o:o['col0']),(cue,other)):
            for r,c in obj['cells']:witness[r][c]=color
    # Both original semantic color contrasts remain; the first existing geometry
    # additionally teaches midpoint grouping and top-row-vs-left-column order.
    train=[witness,old['train'][1],*old['train'][2:]]
    queries=old['test'] if seed%2==0 else incoming['test']
    return {'train':train,'test':queries}

def generate(seed,settings,demos=3,queries=4):
    source=program(settings)
    COLOR._native._integer(seed,0,2**63-1,'seed');COLOR._native._integer(demos,2,6,'demos');COLOR._native._integer(queries,1,4,'queries')
    inputs=_inputs(seed)
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge() as bridge:
        if bridge.runtime_identity.get('protected') is not True:raise RuntimeError('protected Racket required')
        result={split:[{'input':deepcopy(g),'output':COLOR._native.execute(source,g,bridge)} for g in inputs[split][:count]] for split,count in (('train',demos),('test',queries))}
    return {**result,'program_solution':source}

def public_turn(episode,query_index=0):return COLOR._native.public_turn(episode,query_index)
