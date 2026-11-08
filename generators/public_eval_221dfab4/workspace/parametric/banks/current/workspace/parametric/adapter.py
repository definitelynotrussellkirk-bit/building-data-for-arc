"""Native unapproved-authoring adapter; private settings and four-query bank."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
from pathlib import Path
import sys
from puzzle_generators.base import stable_rng

BASE = Path(__file__).resolve().parent
_name = '_family221_' + hashlib.sha256(str(BASE).encode()).hexdigest()[:16]
_spec = importlib.util.spec_from_file_location(_name, BASE/'family.py')
family = importlib.util.module_from_spec(_spec)
sys.modules[_name] = family
_spec.loader.exec_module(family)


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {'extension'}
            or type(settings['extension']) is not str or settings['extension'] not in ('slice','component')):
        raise ValueError('settings must be exactly extension=slice|component')
    return settings['extension']


def program(settings):
    extension = _settings(settings)
    return (BASE/('canonical.rkt' if extension=='slice' else 'component.rkt')).read_text()


def generate(seed, settings, demos, queries):
    extension = _settings(settings)
    family.integer(seed,0,2**63-1,'seed')
    family.integer(demos,2,6,'demos'); family.integer(queries,1,4,'queries')
    shapes = [(12,14),(13,15),(16,18),(17,19),(20,22),(22,24)]
    qshapes = [(14,16),(18,20),(24,27),(30,30)]
    def pair(index, shape):
        g = family.sample(seed,index,*shape)
        return {'input':g, 'output':family.solve(g,extension)}
    train = [pair(i,shapes[i]) for i in range(demos)]
    bank = [pair(100+i,shape) for i,shape in enumerate(qshapes)]
    return {'train':train, 'test':copy.deepcopy(bank[:queries]),
            'private_query_bank':bank, 'program_solution':program(settings)}


def presentation_order(presentation_seed):
    family.integer(presentation_seed,0,2**63-1,'presentation_seed')
    order = list(range(4))
    stable_rng(presentation_seed,'four-query-presentation','1').shuffle(order)
    return order


def public_view(episode, source_query_index):
    """One visible query only. Call with a privately shuffled source index."""
    from reviewer_support import public_challenge_bytes
    import json
    family.integer(source_query_index,0,3,'source_query_index')
    bank = episode['private_query_bank']
    if type(bank) is not list or len(bank)!=4:
        raise ValueError('controller must retain exactly four queries')
    return json.loads(public_challenge_bytes({'train':episode['train'],
                      'test':[{'input':bank[source_query_index]['input']}]}))

CAUSAL_DESCRIPTIONS = {
    'step_a': 'Recover the marker frame, form every sixth-depth green stripe, and intersect original four-connected foreground components with that stripe mask.',
    'intermediate': 'The marker-derived green-depth list and per-component hit flags/cell sets selecting whole foreground objects.',
    'step_b': 'Recolor only the selected component cells outside the projected band; render the marker stripe pattern with precedence inside the band.',
    'why_b_depends_on_a': 'Equal-colored disconnected objects can be hit or missed. The later spatial recoloring needs the computed stripe/component intersection, not just the foreground color or a fixed list of objects.'}


def counterfactual_program():
    text=program({'extension':'component'})
    needle='''(any? (lambda (p) (= (modulo (depth (first p) (second p)) 6) 4))
                                  (obj-cells o))'''
    if text.count(needle)!=1:raise ValueError('component selection source changed')
    return text.replace(needle,'#t')


def causal_settings():
    return {'extension':'component'}


def causal_intermediate(grid):
    return family.intermediate(grid)
