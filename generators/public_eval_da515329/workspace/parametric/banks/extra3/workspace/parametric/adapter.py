"""Native adapter for the da515329 spiral family."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
BASE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_da515329_family_adapter',BASE/'family.py')
family=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=family;_spec.loader.exec_module(family)
CAUSAL_DESCRIPTIONS={
 'step_a':'Complete the four rotationally coupled contact-avoiding spiral arms on the unbounded lattice and clip them to the canvas.',
 'intermediate':'The completed clipped spiral partitioned into four-connected path components with their exact occupied-cell counts.',
 'step_b':'Select the unique largest completed component and recolor all of its cells with color 2.',
 'why_b_depends_on_a':'The raw cross arms are equal; only the completed and clipped spiral reveals which component is longest.'}
def _setting(settings):
    if type(settings) is not dict or set(settings)!={'finish_rule'} or type(settings['finish_rule']) is not str or settings['finish_rule'] not in family.SETTINGS:
        raise ValueError('Expected exactly finish_rule=spiral_only|highlight_longest')
    return settings['finish_rule']
def program(settings):return (BASE/('canonical.rkt' if _setting(settings)=='spiral_only' else 'highlight_longest.rkt')).read_text()
def _integer(value,low,high,name):
    if type(value) is not int or not low<=value<=high:raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value
def _order(seed,tag):
    _integer(seed,0,2**63-1,'seed')
    digest=hashlib.sha256(f'da515329|{tag}|{seed}'.encode()).digest()
    order=list(range(4));random.Random(int.from_bytes(digest,'big')).shuffle(order);return order
def generate(seed,settings,demos=2,queries=4):
    key=_setting(settings);family.validate_request(seed,demos,queries)
    def pair(i,query=False):
        g=family.scene(seed,i,query=query);return {'input':g,'output':family.solve(g,key)}
    bank=[pair(i,True) for i in range(4)]
    order=_order(seed,'native-query-presentation')
    ordered=[bank[index] for index in order]
    return {'train':[pair(i) for i in range(demos)],'test':copy.deepcopy(ordered[:queries]),
            'private_query_bank':bank,'private_query_order':order,
            'program_solution':program(settings)}
def presentation_order(presentation_seed):return _order(_integer(presentation_seed,0,2**63-1,'presentation_seed'),'public-query-presentation')
def public_view(episode,turn=0,presentation_seed=0):
    from reviewer_support import public_challenge_bytes
    _integer(turn,0,3,'turn')
    order=presentation_order(presentation_seed)
    bank=episode.get('private_query_bank')
    if type(bank) is not list or len(bank)!=4:raise ValueError('controller must retain exactly four private queries')
    visible={'train':episode['train'],'test':[{'input':bank[order[turn]]['input']}]}
    return json.loads(public_challenge_bytes(visible))
def causal_settings():return {'finish_rule':'highlight_longest'}
def causal_intermediate(grid):return family.causal_intermediate(grid)
def counterfactual_program():return (BASE/'highlight_shortest.rkt').read_text()
