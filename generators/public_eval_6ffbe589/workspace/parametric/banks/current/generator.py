"""Unapproved cue-count rotation family; labels come from reference.rkt."""
from __future__ import annotations
import importlib.util
from pathlib import Path

RULE_TASK_ID = 'ee_6ffbe589'
VERSION = '1.0.0'
TASK_ID = 'public_eval_6ffbe589'
GENERATOR_ID = TASK_ID
SUMMARY = 'Rotate independently nested colour layers by the number of detached same-colour cue cells.'
INVARIANTS = ['A square radius-two-connected tableau', 'Detached cue cells share tableau colours', 'At least three independently rotatable colour layers']
AXES = {}


def _adapter():
    path = Path(__file__).resolve().parent / 'workspace/parametric/adapter.py'
    spec = importlib.util.spec_from_file_location('_6ffbe589_adapter', path)
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
        bg, r0, c0, side = a.main_box(g)
        turns = a.turn_counts(g)
        if side < 9 or len(turns) < 3 or not any(turns.values()):
            return ['Expected a substantive square tableau with three colours and detached cues']
        for mode in a.MODES:
            a.solve(g, mode)
        return []
    except (ValueError, TypeError, IndexError) as exc:
        return [str(exc)]
