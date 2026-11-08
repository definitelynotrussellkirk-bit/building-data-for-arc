"""Native sidecar with resource-local programs and a portable bound base core."""
from __future__ import annotations
import copy
import importlib.util
from pathlib import Path
import random

HOME = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('_d8e07eb2_native_core', HOME / 'kernel.py')
_core = importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_core)
SETTINGS = _core.SETTINGS
RIVALS = _core.RIVALS
sample = _core.sample
solve = _core.solve
parse = _core.parse
matched_positions = _core.matched_positions
_grid = _core._grid


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {'match'} or
            type(settings['match']) is not str or settings['match'] not in SETTINGS):
        raise ValueError('Expected exactly match=color_shape|shape_only')
    return settings['match']


def program(settings):
    mode = _settings(settings)
    return (HOME / ('canonical.rkt' if mode == 'color_shape' else 'shape_only.rkt')).read_text()


def generate(seed, settings, demos, queries):
    mode = _settings(settings)
    if type(seed) is not int or seed < 0:raise ValueError('Nonnegative exact integer seed required')
    if type(demos) is not int or not 4 <= demos <= 6:raise ValueError('Four to six demonstrations required')
    if type(queries) is not int or not 1 <= queries <= 4:raise ValueError('One to four queries supported')
    def pair(split, index):
        g = sample(seed, split, index)
        return {'input': g, 'output': solve(g, mode)}
    return {'train': [pair('train', i) for i in range(demos)],
            'test': [pair('test', i) for i in range(queries)],
            'program_solution': program(settings)}


def public_views(episode, *, presentation_seed, limit=4):
    if type(presentation_seed) is not int or presentation_seed < 0 or type(limit) is not int or not 1 <= limit <= 4:
        raise ValueError('Invalid public presentation request')
    if len(episode['test']) != 4:
        raise ValueError('Shuffle the complete four-query bank before selecting its prefix')
    order = list(range(4));random.Random(presentation_seed).shuffle(order)
    train = [{'input': _grid(p['input']), 'output': _grid(p['output'])} for p in episode['train']]
    return [copy.deepcopy({'train': train, 'test': [{'input': _grid(episode['test'][i]['input'])}]}) for i in order[:limit]]
