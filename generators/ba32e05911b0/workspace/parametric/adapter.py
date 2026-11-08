"""Two exact rules with seed-selected diversity within every direction."""
from pathlib import Path
import importlib.util
import sys

HOME = Path(__file__).resolve().parent


def _load(relative, label):
    path = HOME / relative
    spec = importlib.util.spec_from_file_location('_ba32_mixture_' + label, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SIX_ROLL = _load('six_roll_adapter.py', 'six_roll')
INTERACTING = _load('interacting/adapter.py', 'interacting')


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def branch(seed):
    _integer(seed, 0, 2**63-1, 'seed')
    return 'six_roll' if seed % 2 == 0 else 'interacting'


def program(settings):
    # Both source modules materialize these same exact two programs.
    return SIX_ROLL.program(settings)


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63-1, 'seed')
    _integer(demos, 2, 6, 'demos')
    _integer(queries, 1, 4, 'queries')
    program(settings)
    if branch(seed) == 'six_roll':
        # The unchanged source accepts four queries. A controller-side prefix
        # exposes any1..4without changing draws, labels or its lesson checks.
        original = SIX_ROLL.generate(seed, settings, demos, 4)
    else:
        original = INTERACTING.generate(seed, settings, demos, queries)
    return {'train': original['train'], 'test': original['test'][:queries],
            'program_solution': program(settings)}


def public_turn(episode, query_index=0):
    return SIX_ROLL._module.public_turn(episode, query_index)
