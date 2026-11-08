"""Unapproved gray-scaffold transfer generator; labels live in reference.rkt."""
from pathlib import Path
import importlib.util

RULE_TASK_ID = 'ee_4c3d4a41'
VERSION = '1.0.0'
TASK_ID = 'public_eval_4c3d4a41'
GENERATOR_ID = TASK_ID
SUMMARY = 'Transfer a gray tooth scaffold into a framed bar field and displace bars above its teeth.'
INVARIANTS = [
    'One size-dominant gray frame and one smaller gray tooth scaffold',
    'Equal ordered counts and pitches of scaffold teeth and colored bars',
    'Rectangular exact-integer grids no larger than 30x30',
]
AXES = {}


def _adapter():
    path = Path(__file__).resolve().parent / 'workspace/parametric/adapter.py'
    spec = importlib.util.spec_from_file_location('_4c3d4a41_generator_adapter', path)
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
        info = a.analyze(value)
        if len(info['bars']) < 3:
            return ['Expected at least three paired bars and teeth']
        if any(bar['visible_length'] < 1 for bar in info['bars']):
            return ['Every displaced bar must retain a visible cell']
        return []
    except (ValueError, TypeError, IndexError) as exc:
        return [str(exc)]
