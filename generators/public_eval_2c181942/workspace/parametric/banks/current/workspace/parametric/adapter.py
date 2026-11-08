"""Source-local native adapter. Returned lessons are private/controller data."""
from pathlib import Path
import copy
import hashlib
import json
import random
import types

BASE=Path(__file__).resolve().parent
G=types.ModuleType('_docking_engine_'+hashlib.sha256(str(BASE).encode()).hexdigest())
G.__file__=str(BASE/'engine.py')
exec(compile((BASE/'engine.py').read_bytes(),G.__file__,'exec'),G.__dict__)


def value(settings):
    if type(settings) is not dict or set(settings)!={'docking'} or type(settings['docking']) is not str or settings['docking'] not in G.VALUES:
        raise ValueError('settings must contain exactly docking: matching|opposite')
    return settings['docking']


def program(settings):
    v=value(settings)
    source=(BASE/'canonical.rkt').read_text()
    return source if v=='matching' else source.replace('(define selection "matching")','(define selection "opposite")',1)


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
    rng=random.Random(int.from_bytes(hashlib.sha256(f'2c181942:presentation:{seed}:{presentation_seed}'.encode()).digest(),'big'))
    rng.shuffle(order)
    return {'public':[{'train':copy.deepcopy(ep['train']),'test':[{'input':copy.deepcopy(ep['test'][i]['input'])}]} for i in order[:queries]],
      'private':{'settings':copy.deepcopy(settings),'program':ep['program_solution'],'seed':seed,'presentation_seed':presentation_seed,
                 'source_indices':order,'source_pairs':copy.deepcopy(ep['test'])}}


def counterfactual_program(settings):
    return rival_program(settings,'other_setting')


def intermediate(g,settings):
    v=value(settings);p,placements=G.placements(g,v)
    _,wrong=G.placements(g,v,'other_setting')
    return {'hub_bbox':list(p['hub_bbox']),'keys_clockwise_from_top':p['keys'],
            'placements':placements,'wrong_matched_slot_placements':wrong,
            'coordinate_system':'absolute canvas coordinates; direction 0=up,1=right,2=down,3=left'}


def dependency():
    return {'step_a':'Decode the four hub keys and, for each matching loose piece, infer the centered neck-facing rotation and translation to its opposite slot.',
      'intermediate':'The input-derived destination side, oriented shape, translation, and final occupied cells for every keyed piece.',
      'step_b':'Erase loose originals, preserve the hub, and stamp each piece color at the cell coordinates supplied by A.',
      'why_b_depends_on_a':'Neither the keyed destination nor the neck orientation can be determined from a fixed color or original compass position. Substituting matching-slot placements changes the assembled scene on the same input.'}
