"""Native authoring adapter; programs, settings and answer banks stay private."""
from pathlib import Path
import importlib.util
import random
import sys

BASE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('_c7_model_' + str(BASE).encode().hex(), BASE / 'prototype.py')
_model = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _model
_spec.loader.exec_module(_model)
SETTINGS = ({'replacement': 'swap'}, {'replacement': 'minority'})


def checked(settings):
    if (type(settings) is not dict or set(settings) != {'replacement'}
            or type(settings['replacement']) is not str or settings not in SETTINGS):
        raise ValueError('expected replacement=swap or replacement=minority')
    return settings['replacement']


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def program(settings):
    replacement = checked(settings)
    source = (BASE / 'canonical.rkt').read_text()
    if replacement == 'swap':
        return source
    old = "(define replacement 'swap)"
    if source.count(old) != 1:
        raise ValueError('expected one canonical replacement declaration')
    return source.replace(old, "(define replacement 'minority)")


def generate(seed, settings, demos=3, queries=4):
    replacement = checked(settings)
    integer(seed, 0, 2**63 - 1, 'seed')
    integer(demos, 2, 6, 'demos')
    integer(queries, 1, 4, 'queries')

    def pair(index, stress=False):
        grid = _model.scene(seed, index, stress=stress)
        return {'input': grid, 'output': _model.solve(grid, replacement=replacement)}

    demonstration_bank = [pair(index) for index in range(6)]
    query_bank = [pair(100 + index, index == 3) for index in range(4)]
    random.Random(f'c7-query-presentation-v1:{seed}').shuffle(query_bank)
    return {'train': demonstration_bank[:demos], 'test': query_bank[:queries],
            'program_solution': program(settings)}
