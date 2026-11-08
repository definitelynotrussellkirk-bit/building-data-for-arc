"""Unapproved multicolor-ship generator; labels live in reference.rkt."""
from pathlib import Path
import importlib.util

RULE_TASK_ID = 'ee_3dc255db'
VERSION = '1.0.0'
TASK_ID = 'public_eval_3dc255db'
GENERATOR_ID = TASK_ID
SUMMARY = 'Remove particles embedded in directional multicolor hulls and eject them from each nose.'
INVARIANTS = [
    'At least two separated 8-connected two-color ships',
    'Each ship has a strict majority hull color and a unique directional nose',
    'Rectangular exact-integer grids no larger than 30x30',
]
AXES = {}


def _adapter():
    path = Path(__file__).resolve().parent / 'workspace/parametric/adapter.py'
    spec = importlib.util.spec_from_file_location('_3dc255db_generator_adapter', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generate(seed, sample_index=0, *, difficulty=None, **overrides):
    if overrides:
        raise ValueError('no controls are declared; unknown overrides are rejected')
    if difficulty not in (None, 'easy', 'medium', 'hard'):
        raise ValueError('invalid difficulty')
    return _adapter().scene(seed, sample_index)


def self_check(value):
    try:
        a = _adapter()
        a.grid(value)
        ships = a.descriptors(value)
        if len(ships) < 2:
            return ['Expected at least two directional ships']
        if any(ship['payload_count'] < 1 for ship in ships):
            return ['Each ship must contain at least one payload particle']
        return []
    except (ValueError, TypeError, IndexError) as exc:
        return [str(exc)]
