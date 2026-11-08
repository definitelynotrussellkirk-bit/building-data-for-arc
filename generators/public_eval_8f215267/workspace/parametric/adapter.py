"""Native graph-connectivity counting family, unapproved until owner admission."""
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
    if type(settings) is not dict or set(settings)!={'connectivity'} or type(settings['connectivity']) is not int or settings['connectivity'] not in (4,8):
        raise ValueError('settings must contain exactly connectivity=4|8')
    return settings['connectivity']


def program(settings):
    con=validate(settings);text=(Path(__file__).resolve().parent/'canonical.rkt').read_text()
    return text if con==4 else text.replace('(define connectivity 4)','(define connectivity 8)')


def generate(seed,settings,demos,queries):
    con=validate(settings);G.integer(seed,0,2**63-1,'seed');G.integer(demos,2,6,'demos');G.integer(queries,1,4,'queries')
    grids=G.bank(seed);pair=lambda g:{'input':deepcopy(g),'output':G.solve(g,con)}
    return {'train':[pair(g) for g in grids[:demos]],'test':[pair(g) for g in grids[6:6+queries]],'program_solution':program(settings)}


def present(seed,settings,demos,queries=4,*,presentation_seed=0):
    """Return a controller-only bundle, never an all-query model prompt."""
    G.integer(queries,1,4,'queries');G.integer(presentation_seed,0,2**63-1,'presentation_seed')
    ep=generate(seed,settings,demos,4);order=list(range(4))
    random.Random(int.from_bytes(sha256(f'{seed}:{presentation_seed}:presentation'.encode()).digest(),'big')).shuffle(order)
    views=[{'train':deepcopy(ep['train']),'test':[{'input':deepcopy(ep['test'][i]['input'])}]} for i in order[:queries]]
    return {'public':views,'private':{'source_indices':order,'seed':seed,'presentation_seed':presentation_seed,
            'settings':deepcopy(settings),'program':ep['program_solution'],'source_pairs':deepcopy(ep['test'])}}


def rival_program(settings,rival):
    con=validate(settings);text=program(settings)
    if rival not in G.RIVALS:raise ValueError('Unknown rival')
    if rival=='opposite_connectivity':return program({'connectivity':12-con})
    old,new={
        'pixel_count_capped':('(define raw-count (length matches))','(define raw-count (apply + (map obj-size matches)))'),
        'distinct_sizes':('(define raw-count (length matches))','(define raw-count (length (remove-duplicates (map obj-size matches))))'),
        'ignore_singletons':('(define raw-count (length matches))','(define raw-count (count-if (lambda (o) (> (obj-size o) 1)) matches))'),
        'only_rectangular':('(define raw-count (length matches))','(define raw-count (count-if (lambda (o) (= (obj-size o) (* (obj-h o) (obj-w o)))) matches))'),
        'presence_only':('(define n raw-count)','(define n (min 1 raw-count))'),
        'global_count':('(define n raw-count)','(define n (length pieces))'),
        'include_frames':('(define n raw-count)','(define n (+ raw-count 1))'),
        'sorted_color_counts':('(define key-color (obj-color f))','(define key-color (obj-color (list-ref (sort frames (lambda (a b) (< (obj-color a) (obj-color b)))) index)))'),
        'left_aligned':('(- (obj-c2 f) (* 2 k))','(+ (obj-c1 f) (* 2 k))'),
        'keep_external':('(define base (empty-grid (rows g) (cols g) bg))','(define base g)'),
    }[rival]
    if text.count(old)!=1:raise ValueError('Reference anchor drift')
    return text.replace(old,new)


def dependency():
    return {
        'step_a':'Identify and remove the hollow frames from the analysis grid, segment the remaining same-color graph with the episode connectivity, and count components for each frame color.',
        'intermediate':'The input-derived vector of external connected-component counts indexed by spatially ordered frame identities and colors.',
        'step_b':'For each frame, place exactly its count of separated color-matched tally dots on the middle row, working from the right interior margin.',
        'why_b_depends_on_a':'The topology-dependent component count determines how many distinct dot positions are painted; neither object area nor color presence supplies that count. Changing one count changes its frame tally while all geometry and colors stay fixed.'}


def counterfactual_program(settings):
    return program(settings).replace('(define n raw-count)','(define n (if (= index 0) (+ raw-count 1) raw-count))')


def intermediate(grid,settings):
    facts=G.measure(grid,validate(settings))
    wrong=facts['counts'][:];wrong[0]+=1
    return {'frame_bboxes':[list(f['bbox']) for f in facts['frames']],
            'frame_colors':[f['color'] for f in facts['frames']],
            'counts':facts['counts'],'wrong_counts':wrong,'connectivity':settings['connectivity']}
