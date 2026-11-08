"""Native adapter: a setting changes only the sink direction, never input RNG."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location('_gates_'+hashlib.sha256(str(HOME).encode()).hexdigest(), HOME/'generator.py')
CORE = importlib.util.module_from_spec(_SPEC); sys.modules[_SPEC.name] = CORE; _SPEC.loader.exec_module(CORE)
RIVALS = ('alternate', 'identity', 'rotation_only', 'one_token_per_track',
          'row_sort', 'edge_sinks_only', 'largest_track_only', 'skip_rotation_topology')


def validate_settings(settings):
    if type(settings) is not dict or set(settings) != {'sink'} or type(settings['sink']) is not str or settings['sink'] not in ('lower', 'upper'):
        raise ValueError('Expected exactly {sink: lower|upper}')
    return settings['sink']


def program(settings):
    sink = validate_settings(settings)
    source = (HOME/'reference.rkt').read_text()
    return source if sink == 'lower' else source.replace('(define prefer-lower? #t)', '(define prefer-lower? #f)')


def surviving_rules(demos, sink):
    survivors = ['intended']
    for name in RIVALS:
        def predict(g):
            return CORE.solve(g, 'upper' if sink == 'lower' else 'lower') if name == 'alternate' else CORE.solve(g, sink, rival=name)
        if all(predict(p['input']) == p['output'] for p in demos):
            survivors.append(name)
    return survivors


def _train_bank(seed):
    shapes = ((11, 15), (13, 17), (15, 19), (17, 21), (19, 23), (21, 25))
    for attempt in range(64):
        first = [CORE.sample_input(CORE.rng_for(seed, 'train', i, attempt), *shapes[i]) for i in range(2)]
        if all(surviving_rules([{'input':g,'output':CORE.solve(g,s)} for g in first],s) == ['intended'] for s in ('lower','upper')):
            return first + [CORE.sample_input(CORE.rng_for(seed,'train',i,attempt),*shapes[i]) for i in range(2,6)]
    raise RuntimeError('Finite-rival teaching sampler exhausted 64 attempts')


def generate(seed, settings, demos, queries):
    sink = validate_settings(settings)
    for value, low, high, name in ((seed,0,2**63-1,'seed'),(demos,2,6,'demos'),(queries,1,4,'queries')):
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    train = _train_bank(seed)
    test = [CORE.sample_input(CORE.rng_for(seed,'query',i), *shape)
            for i,shape in enumerate(((13,17),(17,23),(23,27),(30,30)))]
    if len({json.dumps(g) for g in train+test}) != 10:
        raise RuntimeError('Generated inputs collided')
    pair = lambda g: {'input':g,'output':CORE.solve(g,sink)}
    return {'train':[pair(g) for g in train[:demos]], 'test':[pair(g) for g in test[:queries]],
            'program_solution':program(settings)}
