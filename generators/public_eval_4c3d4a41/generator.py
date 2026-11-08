"""Unapproved public-parent comb insertion input generator."""
from pathlib import Path
import importlib.util
RULE_TASK_ID = 'ee_4c3d4a41'
VERSION = '1.0.0'
TASK_ID = GENERATOR_ID = 'public_eval_4c3d4a41'
SUMMARY = 'Insert a gray comb into an upright container and push obstructed stacks upward, clipping overflow.'
AXES = {}
INVARIANTS = ['One upright open-sided container and one separate comb',
              'Four to six colored lanes with contiguous stacks and gray caps',
              'All cells exact integers in 0..9; all dimensions at most 30',
              'Curriculum varies the original rank of the surviving-longest lane']


def _adapter():
    path=Path(__file__).resolve().parent/'workspace/parametric/adapter.py'
    spec=importlib.util.spec_from_file_location('_comb_4c3d4a41',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def generate(seed, sample_index=0, *, difficulty=None, **overrides):
    if overrides:raise ValueError('no override controls are declared')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('invalid difficulty')
    return _adapter().scene(seed,sample_index)


def self_check(g, *, difficulty=None):
    try:
        _adapter().extract(g)
        return []
    except (ValueError,TypeError,IndexError) as exc:
        return [str(exc)]
