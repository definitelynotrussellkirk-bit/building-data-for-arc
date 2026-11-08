"""Source-local native adapter. Returned lessons are private/controller data."""
from pathlib import Path
import copy
import hashlib
import json
import random
import types

BASE=Path(__file__).resolve().parent
G=types.ModuleType('_stencil_engine_'+hashlib.sha256(str(BASE).encode()).hexdigest())
G.__file__=str(BASE/'engine.py')
exec(compile((BASE/'engine.py').read_bytes(),G.__file__,'exec'),G.__dict__)


def value(settings):
    if type(settings) is not dict or set(settings)!={'mask_rule'} or type(settings['mask_rule']) is not str or settings['mask_rule'] not in G.VALUES:
        raise ValueError('settings must contain exactly mask_rule: all|largest')
    return settings['mask_rule']


def program(settings):
    v=value(settings)
    source=(BASE/'canonical.rkt').read_text()
    return source if v=='all' else source.replace('(define selection "all")','(define selection "largest")',1)


def rival_program(settings,rival):
    if rival not in G.RIVALS:raise ValueError('Unknown rival')
    return program(settings).replace('(define rival "")',f'(define rival "{rival}")',1)


def generate(seed,settings,demos=2,queries=4):
    v=value(settings);G.integer(seed,0,2**63-1,'seed');G.integer(demos,2,6,'demos');G.integer(queries,1,4,'queries')
    ds,qs=G.input_bank(seed)
    def pair(text):
        g=json.loads(text);return {'input':g,'output':G.solve(g,v)}
    return {'train':[pair(g) for g in ds[:demos]],'test':[pair(g) for g in qs[:queries]],'program_solution':program(settings)}


def present(seed,settings,demos=2,queries=4,presentation_seed=0):
    G.integer(queries,1,4,'queries');G.integer(presentation_seed,0,2**63-1,'presentation_seed')
    ep=generate(seed,settings,demos,4);order=list(range(4))
    rng=random.Random(int.from_bytes(hashlib.sha256(f'bf45cf4b:presentation:{seed}:{presentation_seed}'.encode()).digest(),'big'))
    rng.shuffle(order)
    return {'public':[{'train':copy.deepcopy(ep['train']),'test':[{'input':copy.deepcopy(ep['test'][i]['input'])}]} for i in order[:queries]],
      'private':{'settings':copy.deepcopy(settings),'program':ep['program_solution'],'seed':seed,'presentation_seed':presentation_seed,
                 'source_indices':order,'source_pairs':copy.deepcopy(ep['test'])}}


def counterfactual_program(settings):
    return rival_program(settings,'smallest_component')


def intermediate(g,settings):
    value(settings);p=G.parse(g);selected=max(p['regions'],key=len)
    return {'stencil_bbox':list(p['mask_bbox']),'tile_bbox':list(p['tile_bbox']),
            'component_sizes':list(map(len,p['regions'])),'selected_cells':[list(x) for x in selected],
            'wrong_selected_cells':[list(x) for x in min(p['regions'],key=len)],
            'coordinate_system':'relative to original tight stencil; output box not recropped'}


def dependency():
    return {'step_a':'Identify the monochrome stencil and multicolor tile, segment the stencil into four-connected regions, and select its largest region.',
      'intermediate':'The selected region cell coordinates within the original tight stencil bounding box, plus the cropped tile.',
      'step_b':'Expand selected stencil cells into complete tile blocks and all other stencil positions into equally sized background blocks.',
      'why_b_depends_on_a':'The output block positions depend on which input-dependent region A selects. Substituting the smallest region changes the mosaic while retaining the input, tile, and output canvas.'}
