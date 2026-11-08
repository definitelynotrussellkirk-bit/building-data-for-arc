"""Unapproved triomino-pointer family; labels come from reference.rkt."""
from __future__ import annotations
import importlib.util
from pathlib import Path

RULE_TASK_ID = 'ee_409aa875'
VERSION = '1.0.0'
TASK_ID = 'public_eval_409aa875'
GENERATOR_ID = TASK_ID
SUMMARY = 'Project five cells from oriented triomino pointers, resolving endpoint collisions and struck objects.'
INVARIANTS = ['Every foreground component is a three-cell pointer', 'Pointer endpoints remain within the 1..30 canvas for both settings', 'Lessons contain collisions and object hits']
AXES = {}


def _adapter():
    path = Path(__file__).resolve().parent / 'workspace/parametric/adapter.py'
    spec = importlib.util.spec_from_file_location('_409aa875_adapter', path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def generate(seed, sample_index=0, *, difficulty=None, **overrides):
    if overrides:
        raise ValueError('no controls are declared; unknown overrides are rejected')
    if difficulty not in (None, 'easy', 'medium', 'hard'):
        raise ValueError('invalid difficulty')
    return _adapter().scene(seed, sample_index)


def self_check(g):
    try:
        a = _adapter()
        a.grid(g)
        _, objects, _, _ = a.analyze(g, 'forward')
        if len(objects) < 5:
            return ['Expected at least five separate triomino pointers']
        for mode in a.MODES:
            a.solve(g, mode)
        return []
    except (ValueError, TypeError, IndexError) as exc:
        return [str(exc)]
