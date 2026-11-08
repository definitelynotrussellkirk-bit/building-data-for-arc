"""Native, deterministic adapter; labels are independently re-executed by Racket."""
from pathlib import Path
from copy import deepcopy
import hashlib, importlib.util, json, random, sys
BASE=Path(__file__).resolve().parent
_name='_donor_family_'+hashlib.sha256(str(BASE).encode()).hexdigest()
_spec=importlib.util.spec_from_file_location(_name,BASE/'family.py')
family=importlib.util.module_from_spec(_spec);sys.modules[_name]=family;_spec.loader.exec_module(family)


def validate(settings):
    if type(settings) is not dict or set(settings)!={'aggregation'} or type(settings['aggregation']) is not str or settings['aggregation'] not in family.POLICIES:
        raise ValueError('settings must be exactly aggregation=sum|maximum')
    return settings['aggregation']


def program(settings):
    policy=validate(settings)
    source=(BASE/'canonical.rkt').read_text()
    if policy=='maximum':
        source=source.replace('(define amount (apply + donor-counts))','(define amount (apply max donor-counts))')
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

PARAMETER='aggregation'

def causal_case():
    settings={'aggregation':'sum'}
    e=generate(17,settings,2,4);grid=e['test'][3]['input'];state=family.parse(grid)
    source=program(settings)
    return dict(input=grid,settings=settings,program=source,
                intermediate_value={'donor_counts':state['donor_counts'],'amount':sum(state['donor_counts']),
                                    'receiver_top_row':state['top']['r1'],'pitch':state['pitch']},
                counterfactual_program=source.replace('(define amount (apply + donor-counts))','(define amount 1)'),
                ablation='wrong_intermediate',
                step_a='Locate command bars and aligned stacks; count donor objects and measure the receiver pitch.',
                intermediate='Ordered donor-count vector, aggregated transfer count, and receiver shape/pitch.',
                step_b='Gray donors, erase bars, and add the computed count of receiver-shaped copies above the top receiver.',
                why_b_depends_on_a='The number and placement of new receiver copies depend on input-specific donor counts and receiver geometry, not just marker colors.')
