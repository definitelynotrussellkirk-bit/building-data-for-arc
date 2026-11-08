"""Canonical production entry for public ARC parent f560132c."""
from pathlib import Path
import importlib.util
import sys
from puzzle_generators.base import gen_ctx

RULE_TASK_ID = 'ee_f560132c'
VERSION = '1.0.0'
TASK_ID = 'public_eval_f560132c'
GENERATOR_ID = TASK_ID
SUMMARY = 'Rotate disconnected palette-indexed pieces into an exact square tiling.'
INVARIANTS = ['Four or nine pieces', 'One embedded distinct palette', 'No reflections']
AXES = {}

_spec = importlib.util.spec_from_file_location('_f560132c_prototype', Path(__file__).resolve().parent/'workspace/parametric/prototype.py')
P = importlib.util.module_from_spec(_spec); sys.modules[_spec.name] = P; _spec.loader.exec_module(P)


def generate(seed, sample_index=0, difficulty=None, **overrides):
    if overrides:
        raise ValueError(f'Unsupported overrides: {sorted(overrides)}')
    if difficulty not in (None, 'easy', 'medium', 'hard'):
        raise ValueError('Unknown difficulty')
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides={})
    return P.scene(seed, sample_index, rng=ctx.draw_rng('jigsaw'))


def self_check(grid, **_):
    return P.self_check(grid)
