"""Native adapter; canonical sampler/semantics live in the portable base generator."""
from __future__ import annotations
import copy
import importlib.util
from pathlib import Path
import random
HOME=Path(__file__).resolve().parents[2]
_spec=importlib.util.spec_from_file_location('_native_core_'+HOME.name,HOME/'generator.py')
_core=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_core)
SETTINGS=_core.SETTINGS
sample=_core.sample
solve=_core.solve
parse=_core.parse
_grid=_core._grid
holes=_core.holes
components=_core.components


def _validate_settings(settings):
    if type(settings) is not dict or set(settings)!={'lookup'} or settings['lookup'] not in SETTINGS:
        raise ValueError('Expected exactly one lookup setting')
    return settings['lookup']


def program(settings):
    lookup=_validate_settings(settings)
    p=HOME/'reference.rkt' if lookup=='exact' else Path(__file__).with_name('nearest_lower.rkt')
    return p.read_text()


def generate(seed,settings,demos,queries):
    lookup=_validate_settings(settings)
    if type(seed) is not int or seed<0:raise ValueError('seed must be a nonnegative exact integer')
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos must be 2..6')
    if type(queries) is not int or not 1<=queries<=4:raise ValueError('queries must be 1..4')
    def pair(split,index):
        g=sample(seed,split,index);return {'input':g,'output':solve(g,lookup)}
    return {'train':[pair('train',i) for i in range(demos)],'test':[pair('test',i) for i in range(queries)],'program_solution':program(settings)}


def public_views(episode,*,presentation_seed,limit=4):
    if type(presentation_seed) is not int or type(limit) is not int or not 1<=limit<=4:raise ValueError('Invalid presentation request')
    if len(episode['test'])!=4:raise ValueError('Shuffle the complete four-query bank before selecting a prefix')
    order=list(range(4));random.Random(presentation_seed).shuffle(order)
    train=[{'input':_grid(p['input']),'output':_grid(p['output'])} for p in episode['train']]
    return [copy.deepcopy({'train':train,'test':[{'input':_grid(episode['test'][i]['input'])}]}) for i in order[:limit]]

