"""Fresh nested tile-mask completion inputs for public parent b99e7126."""
from pathlib import Path
import importlib.util
import sys

from puzzle_generators.base import gen_ctx

RULE_TASK_ID = 'ee_b99e7126'
VERSION = '1.0.0'
TASK_ID = GENERATOR_ID = 'public_eval_b99e7126'
SUMMARY = 'Use the unique color inside a rare tile as a macro-mask and complete its translated tile arrangement.'
INVARIANTS = [
    'Uniform separator lattice around equal square tiles',
    'Exactly one common tile pattern and one rare tile pattern',
    'Rare tile contains one color absent from the common tile',
]
AXES = {}

_spec = importlib.util.spec_from_file_location(
    '_b99e7126_family', Path(__file__).resolve().parent / 'workspace/parametric/family.py'
)
F = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = F
_spec.loader.exec_module(F)


def generate(seed, sample_index=0, difficulty=None, **overrides):
    if overrides:
        raise ValueError(f'Unsupported overrides: {sorted(overrides)}')
    if difficulty not in (None, 'easy', 'medium', 'hard'):
        raise ValueError('Unknown difficulty')
    gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides={},
    )
    return F.scene(seed, sample_index, query=False)


def self_check(grid):
    try:
        F.analyze(grid)
        intermediate = F.causal_intermediate(grid)
        return [] if intermediate['completed_densest_row'] != intermediate['visible_densest_row'] else [
            'Visible and completed densest rows must differ'
        ]
    except (ValueError, TypeError) as exc:
        return [str(exc)]
