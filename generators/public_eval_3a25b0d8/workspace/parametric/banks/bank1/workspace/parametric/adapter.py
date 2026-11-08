"""Native, deterministic adapter; labels are independently re-executed by Racket."""
from pathlib import Path
from copy import deepcopy
import hashlib, importlib.util, json, random, sys
BASE=Path(__file__).resolve().parent
_name='_compartment_family_'+hashlib.sha256(str(BASE).encode()).hexdigest()
_spec=importlib.util.spec_from_file_location(_name,BASE/'family.py')
family=importlib.util.module_from_spec(_spec);sys.modules[_name]=family;_spec.loader.exec_module(family)


def validate(settings):
    if type(settings) is not dict or set(settings)!={'color_order'} or type(settings['color_order']) is not str or settings['color_order'] not in family.POLICIES:
        raise ValueError('settings must be exactly color_order=aligned|reverse_vertical')
    return settings['color_order']


def program(settings):
    policy=validate(settings)
    source=(BASE/'canonical.rkt').read_text()
    if policy=='reverse_vertical':
        source=source.replace('(define reverse-order? #f)','(define reverse-order? #t)')
    return source


def generate(seed,settings,demos,queries):
    policy=validate(settings)
    family.integer(seed,0,2**63-1,'seed');family.integer(demos,2,6,'demos');family.integer(queries,1,4,'queries')
    def pair(i):
        g=family.make_scene(seed,i)
        return {'input':g,'output':family.solve(g,policy)}
    # Build the whole private bank first; queries are independent of demo count.
    bank=[pair(i) for i in range(6,10)]
    return {'train':[pair(i) for i in range(demos)],'test':bank[:queries],
            'program_solution':program(settings)}


def public_views(episode,presentation_seed):
    """Controller-only: shuffle all four inputs, then reveal one view at a time.

    Never expose the returned list, its length, or a directory listing to the
    model. Callers must retain the entire four-query private episode.
    """
    family.integer(presentation_seed,0,2**63-1,'presentation_seed')
    if type(episode) is not dict or type(episode.get('test')) is not list or len(episode['test'])!=4:
        raise ValueError('public presentation requires the complete four-query bank')
    order=list(range(4));random.Random(presentation_seed).shuffle(order)
    return [deepcopy({'train':[{'input':p['input'],'output':p['output']} for p in episode['train']],
                      'test':[{'input':episode['test'][i]['input']}]}) for i in order]


PARAMETER='color_order'

def causal_case():
    settings={'color_order':'reverse_vertical'}
    e=generate(17,settings,2,4);grid=e['test'][3]['input'];state=family.parse(grid)
    source=program(settings)
    return dict(input=grid,settings=settings,program=source,
                intermediate_value={'target_lane_and_box':[{'side':o['side'],'box':list(o['box'])} for o in state['target_regions']],
                                    'ordered_source_colors':family.assign(state,'reverse_vertical')},
                counterfactual_program=source.replace('(define source-regions (ordered source reverse-order?))',
                    '(define source-regions (map (lambda (t) (first (ordered source reverse-order?))) target-regions))'),
                ablation='wrong_intermediate',
                step_a='Isolate figures, extract enclosed four-connected regions, and form the ordered lane-specific source-color correspondence.',
                intermediate='Target compartment lane/ordinal vector paired with input-dependent source compartment colors.',
                step_b='Fill each target compartment with its matched source color and return the isolated target crop.',
                why_b_depends_on_a='Target geometry alone does not specify colors; rendering needs the measured source compartment correspondence, including lane and vertical order.')
