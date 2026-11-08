"""Native unapproved-authoring adapter for legend-ordered framed routes."""
from __future__ import annotations
import copy,hashlib,importlib.util,json
from pathlib import Path
import sys
from puzzle_generators.base import stable_rng
BASE=Path(__file__).resolve().parent
_name='_family3e_'+hashlib.sha256(str(BASE).encode()).hexdigest()[:16]
_spec=importlib.util.spec_from_file_location(_name,BASE/'family.py')
family=importlib.util.module_from_spec(_spec);sys.modules[_name]=family;_spec.loader.exec_module(family)


def _settings(settings):
    if (type(settings) is not dict or set(settings)!={'bridge_color'} or type(settings['bridge_color']) is not str
            or settings['bridge_color'] not in ('source','destination')):
        raise ValueError('settings must be exactly bridge_color=source|destination')
    return settings['bridge_color']


def program(settings):
    value=_settings(settings)
    return (BASE/('canonical.rkt' if value=='source' else 'destination.rkt')).read_text()


def generate(seed,settings,demos,queries):
    value=_settings(settings)
    family.integer(seed,0,2**63-1,'seed');family.integer(demos,2,6,'demos');family.integer(queries,1,4,'queries')
    shapes=[(14,17),(18,20),(20,23),(22,25),(24,27),(26,29)]
    qshapes=[(16,19),(20,23),(24,27),(30,30)]
    def pair(index,shape):
        g=family.sample(seed,index,*shape)
        return {'input':g,'output':family.solve(g,value)}
    train=[pair(i,shapes[i]) for i in range(demos)]
    bank=[pair(100+i,shape) for i,shape in enumerate(qshapes)]
    return {'train':train,'test':copy.deepcopy(bank[:queries]),'private_query_bank':bank,
            'program_solution':program(settings)}


def presentation_order(presentation_seed):
    family.integer(presentation_seed,0,2**63-1,'presentation_seed')
    order=list(range(4));stable_rng(presentation_seed,'four-query-presentation','1').shuffle(order);return order


def public_view(episode,source_query_index):
    from reviewer_support import public_challenge_bytes
    family.integer(source_query_index,0,3,'source_query_index')
    bank=episode['private_query_bank']
    if type(bank) is not list or len(bank)!=4:raise ValueError('private four-query bank required')
    return json.loads(public_challenge_bytes({'train':episode['train'],'test':[{'input':bank[source_query_index]['input']}]}))


CAUSAL_DESCRIPTIONS={
 'step_a':'Read the detached singleton legend and occurrence-match each color to the corresponding framed block in block reading order.',
 'intermediate':'The ordered route of input-dependent block records, including payload colors and frame/payload bounding boxes.',
 'step_b':'For each consecutive route pair, paint the empty aligned corridor at payload thickness using the episode endpoint-color policy.',
 'why_b_depends_on_a':'The spatial block reading order is deliberately not the route order, repeated payload colors require occurrence matching, and unused spatial adjacencies are decoys. Corridor painting needs the decoded route.'}


def causal_settings():return {'bridge_color':'destination'}

def causal_intermediate(grid):return family.intermediate(grid)

def counterfactual_program():
    text=program(causal_settings())
    start='   (define route\n    (for/list ((color sequence) (i (range (length sequence))))\n     (define occurrence\n      (count-if (lambda (v) (= v color)) (take sequence i)))\n     (list-ref (filter (lambda (b) (= (first b) color)) blocks) occurrence)))'
    if text.count(start)!=1:raise ValueError('route consumer source changed')
    return text.replace(start,'   (define route blocks)')
