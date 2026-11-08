"""Native adapter; claim labels are independently re-executed by preflight."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
from pathlib import Path
import random
import sys

HOME=Path(__file__).resolve().parents[2]
_source=HOME/'generator.py'
_body=_source.read_bytes()
# Both path and exact content identify the module; timestamps/pyc caches cannot
# turn live edited bytes into a stale, incorrectly source-bound implementation.
_name='_family_'+sha256(str(_source).encode()+b'\0'+_body).hexdigest()
if _name not in sys.modules:
    _spec=importlib.util.spec_from_file_location(_name,_source)
    _module=importlib.util.module_from_spec(_spec)
    sys.modules[_name]=_module
    try:
        exec(compile(_body,str(_source),'exec'),_module.__dict__)
    except BaseException:
        sys.modules.pop(_name,None)
        raise
G=sys.modules[_name]


def validate(settings):
    if type(settings) is not dict or set(settings)!={'turn'} or type(settings['turn']) is not str or settings['turn'] not in ('north','south'):
        raise ValueError('settings must contain exactly turn=north|south')
    return settings['turn']


def program(settings):
    turn=validate(settings); text=(Path(__file__).resolve().parent/'canonical.rkt').read_text()
    return text if turn=='north' else text.replace('(define vertical-step -1)','(define vertical-step 1)')


def generate(seed,settings,demos,queries):
    turn=validate(settings); G.integer(seed,0,2**63-1,'seed')
    G.integer(demos,2,6,'demos'); G.integer(queries,1,4,'queries')
    grids=G.bank(seed)
    pair=lambda g:{'input':deepcopy(g),'output':G.solve(g,turn)}
    return {'train':[pair(g) for g in grids[:demos]],'test':[pair(g) for g in grids[6:6+queries]],'program_solution':program(settings)}


def present(seed,settings,demos,queries=4,*,presentation_seed=0):
    """Controller-only bundle. Give the model ONE public view at a time."""
    G.integer(queries,1,4,'queries'); G.integer(presentation_seed,0,2**63-1,'presentation_seed')
    lesson=generate(seed,settings,demos,4)
    order=list(range(4))
    rng=random.Random(int.from_bytes(sha256(f'{seed}:{presentation_seed}:presentation'.encode()).digest(),'big'))
    rng.shuffle(order)
    views=[{'train':deepcopy(lesson['train']),'test':[{'input':deepcopy(lesson['test'][i]['input'])}]} for i in order[:queries]]
    return {'public':views,'private':{'source_indices':order,'seed':seed,'presentation_seed':presentation_seed,
            'settings':deepcopy(settings),'program':lesson['program_solution'],'source_pairs':deepcopy(lesson['test'])}}


def rival_program(settings,rival):
    """Executable, finite self-review rivals; not promoted settings."""
    turn=validate(settings); text=program(settings)
    if rival not in G.RIVALS: raise ValueError('Unknown rival')
    if rival=='opposite_turn': return program({'turn':'south' if turn=='north' else 'north'})
    old,new={
        'stop_first':('(if (free? tr tc)','(if #f'),
        'reverse_sequence':('(define pattern raw-pattern)','(define pattern (reverse raw-pattern))'),
        'deduplicate_sequence':('(define pattern raw-pattern)','(define pattern (remove-duplicates raw-pattern))'),
        'first_color_only':('(define pattern raw-pattern)','(define pattern (take raw-pattern 1))'),
        'keep_legend':('(for/fold ((out clean))','(for/fold ((out g))'),
        'phase_plus_one':('(walk out r 0 0 0','(walk out r 0 0 1'),
        'reset_at_turn':('(walk marked tr tc next-heading (+ phase 1)','(walk marked tr tc next-heading 0'),
        'early_pivot':('(pc c)','(pc (if (and (= heading 0) (> c 0)) (- c 1) c))'),
        'omit_collision':('(set-cell painted nr nc marker)','painted'),
    }[rival]
    if text.count(old)!=1: raise ValueError('Reference anchor drift')
    return text.replace(old,new)


def dependency():
    return {
        'step_a':'Trace the first eastward corridor leg to its first blocked cell and retain the preceding walkable pivot coordinate.',
        'intermediate':'The input-derived first collision pivot (row, column), together with the ongoing sequence phase.',
        'step_b':'Launch the vertical leg from that pivot and continue alternating turns while painting the cyclic legend sequence.',
        'why_b_depends_on_a':'Changing the pivot by one column changes the subsequent vertical collision, later horizontal legs, and final cells; their positions cannot be fixed before tracing the first leg.'}


def counterfactual_program(settings):
    text=program(settings)
    return text.replace('(pc c)','(pc (if (and (= heading 0) (= r (first starts)) (> c 0)) (- c 1) c))')


def intermediate(grid,settings):
    validate(settings); f=G.parse(grid); r,c=f['starts'][0]
    while c+1<len(grid[0]) and grid[r][c+1]==f['road']: c+=1
    return {'first_pivot':[r,c],'wrong_pivot':[r,max(0,c-1)],'phase_at_pivot':c%len(f['pattern']),
            'pattern':f['pattern'],'counterfactual_scope':'first origin, first horizontal collision only'}
